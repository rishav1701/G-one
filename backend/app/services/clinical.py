import hashlib
import json
import re
import uuid
from datetime import timedelta
from decimal import Decimal

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.auth import current_session
from app.core.config import settings
from app.domain.clock import Clock, SystemClock
from app.domain.news2 import PARAMETERS, Assessment, Level, SpO2Scale, calculate_news2
from app.models.base import (
    Admission, ApiKey, AppUser, AuditLog, IngestionRejection, Observation,
    Patient, RiskAssessment, Role, UserWard, Ward,
)
from app.schemas.clinical import ObservationInput

def _audit(db: DBSession, request: Request, actor_id: str | None, action: str, object_type: str, object_id: str | None):
    db.add(AuditLog(
        actor_id=actor_id, action=action, object_type=object_type, object_id=object_id,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
    ))


def _visible_ward_ids(db: DBSession, user: AppUser) -> set[str] | None:
    if user.role is Role.ADMIN:
        return None
    return set(db.scalars(select(UserWard.ward_id).where(UserWard.user_id == user.id)).all())


def _authorized_ingestor(request: Request, db: DBSession) -> tuple[str | None, bool]:
    raw_key = request.headers.get("X-API-Key", "")
    if raw_key:
        key = db.query(ApiKey).filter_by(key_hash=hashlib.sha256(raw_key.encode()).hexdigest(), scope="ingest:write").first()
        if key:
            return None, True
        raise HTTPException(status_code=401, detail="A valid ingestion key is required")
    user = current_session(request, db)
    if user.role not in (Role.CLINICIAN, Role.SENIOR_CLINICIAN):
        raise HTTPException(status_code=403, detail="Access denied")
    return user.id, False


def _reject(db: DBSession, request: Request, admission_id: str | None, code: str, source: str):
    safe_source = source if isinstance(source, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", source) else "unknown"
    clock = getattr(request.app.state, "clock", SystemClock())
    rejection = IngestionRejection(admission_id=admission_id, reason_code=code, source=safe_source, received_at=clock.now())
    db.add(rejection)
    db.flush()
    _audit(db, request, None, "observation.rejected", "ingestion_rejection", rejection.id)
    db.commit()


def _payload_hash(data: ObservationInput) -> str:
    serialized = json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def _validate_hard_ranges(data: ObservationInput) -> bool:
    for name, (minimum, maximum) in settings.observation_hard_limits.items():
        value = getattr(data, name)
        if value is not None and not minimum <= float(value) <= maximum:
            return False
    return any(getattr(data, name) is not None for name in PARAMETERS)


def plausibility_warnings(data: ObservationInput) -> list[str]:
    warnings: list[str] = []
    for name, (minimum, maximum) in settings.observation_plausibility_limits.items():
        value = getattr(data, name)
        if value is not None and not minimum <= float(value) <= maximum:
            warnings.append(name)
    return warnings


def _current_assessment_values(db: DBSession, admission: Admission, now) -> tuple[dict[str, object | None], list[Observation], bool]:
    cutoff = now - timedelta(hours=settings.observation_stale_hours)
    rows = db.scalars(
        select(Observation).where(
            Observation.admission_id == admission.id,
            Observation.status == "VALID",
            Observation.measured_at <= now,
        ).order_by(Observation.measured_at.desc(), Observation.received_at.desc())
    ).all()
    latest: dict[str, object | None] = {name: None for name in PARAMETERS}
    selected: dict[str, Observation] = {}
    newest_any = None
    for row in rows:
        if newest_any is None:
            newest_any = row
        if row.measured_at < cutoff:
            continue
        for name in PARAMETERS:
            if latest[name] is None and getattr(row, name) is not None:
                latest[name] = getattr(row, name)
                selected[name] = row
    return latest, list({row.id: row for row in selected.values()}.values()), bool(newest_any and newest_any.measured_at < cutoff)


def persist_assessment(db: DBSession, admission: Admission, now) -> RiskAssessment:
    values, source_rows, stale = _current_assessment_values(db, admission, now)
    no_data = not source_rows and not stale
    result = calculate_news2(
        values, spo2_scale=SpO2Scale(admission.spo2_scale), stale=stale, no_data=no_data,
    )
    deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "gone-assessment:" + ":".join(sorted(row.id for row in source_rows)))) if source_rows and all(row.is_simulated for row in source_rows) else None
    if deterministic_id:
        existing = db.get(RiskAssessment, deterministic_id)
        if existing:
            return existing
    record = RiskAssessment(
        id=deterministic_id or str(uuid.uuid4()),
        admission_id=admission.id, scoring_version=result.scoring_version,
        spo2_scale=admission.spo2_scale, observation_ids=sorted(row.id for row in source_rows),
        per_parameter_scores=result.scores, completeness=result.completeness,
        level=result.level.value, total=result.total, explanation=result.explanation(), computed_at=now,
    )
    db.add(record)
    return record


def refresh_current_assessment(db: DBSession, admission: Admission, now, request_id: str | None = None) -> RiskAssessment:
    values, source_rows, stale = _current_assessment_values(db, admission, now)
    expected = calculate_news2(
        values, spo2_scale=SpO2Scale(admission.spo2_scale), stale=stale,
        no_data=not source_rows and not stale,
    )
    latest = db.scalar(select(RiskAssessment).where(RiskAssessment.admission_id == admission.id).order_by(RiskAssessment.computed_at.desc()).limit(1))
    ids = sorted(row.id for row in source_rows)
    if latest and latest.observation_ids == ids and latest.explanation == expected.explanation():
        return latest
    assessment = persist_assessment(db, admission, now)
    db.flush()
    from app.services.alerts import apply_assessment_to_alert
    apply_assessment_to_alert(db, admission, assessment, now, request_id=request_id)
    return assessment


def recompute_stored_assessment(db: DBSession, assessment_id: str) -> Assessment:
    record = db.get(RiskAssessment, assessment_id)
    if record is None:
        raise LookupError("Assessment not found")
    rows = db.scalars(select(Observation).where(Observation.id.in_(record.observation_ids))).all() if record.observation_ids else []
    values: dict[str, object | None] = {name: None for name in PARAMETERS}
    for name in PARAMETERS:
        matching = [row for row in rows if getattr(row, name) is not None]
        if matching:
            row = max(matching, key=lambda item: (item.measured_at, item.received_at))
            values[name] = getattr(row, name)
    return calculate_news2(
        values, spo2_scale=SpO2Scale(record.spo2_scale), scoring_version=record.scoring_version,
        stale=record.level == Level.STALE.value, no_data=record.level == Level.NO_DATA.value,
    )


def record_observation(
    db: DBSession, request: Request, payload: dict, clock: Clock | None = None,
) -> tuple[Observation, bool, list[str]]:
    clock = clock or SystemClock()
    actor_id, is_machine = _authorized_ingestor(request, db)
    source = payload.get("source", "unknown") if isinstance(payload, dict) else "unknown"
    admission_id = payload.get("admission_id") if isinstance(payload, dict) else None
    try:
        data = ObservationInput.model_validate(payload)
    except Exception as exc:
        message = str(exc).lower()
        code = "INVALID_PRECISION" if "decimal" in message or "precision" in message else "INVALID_VALUE"
        _reject(db, request, None, code, source)
        raise HTTPException(status_code=422, detail="Observation was rejected") from exc
    admission = db.get(Admission, data.admission_id)
    if admission is None:
        _reject(db, request, data.admission_id, "INVALID_VALUE", data.source)
        raise HTTPException(status_code=404, detail="Admission not found")
    if not is_machine:
        user = db.get(AppUser, actor_id)
        ward_ids = _visible_ward_ids(db, user)
        if admission.ward_id not in (ward_ids or set()):
            raise HTTPException(status_code=404, detail="Admission not found")
    if admission.status != "ACTIVE":
        _reject(db, request, admission.id, "INVALID_VALUE", data.source)
        raise HTTPException(status_code=409, detail="Admission is not active")
    if not _validate_hard_ranges(data):
        _reject(db, request, admission.id, "HARD_RANGE", data.source)
        raise HTTPException(status_code=422, detail="Observation was rejected")
    now = clock.now()
    if data.measured_at > now:
        _reject(db, request, admission.id, "FUTURE_TIMESTAMP", data.source)
        raise HTTPException(status_code=422, detail="Observation was rejected")
    payload_hash = _payload_hash(data)
    existing = db.query(Observation).filter_by(
        admission_id=admission.id, source=data.source, source_record_id=data.source_record_id,
    ).first()
    if existing:
        if existing.payload_hash == payload_hash:
            return existing, True, plausibility_warnings(data)
        _reject(db, request, admission.id, "IDEMPOTENCY_CONFLICT", data.source)
        raise HTTPException(status_code=409, detail="Source record conflicts with an earlier submission")
    row_id = str(uuid.uuid5(uuid.UUID(admission.id), f"{data.source}:{data.source_record_id}")) if data.is_simulated else str(uuid.uuid4())
    row = Observation(
        id=row_id, admission_id=admission.id, measured_at=data.measured_at,
        received_at=now, respiration_rate=data.respiration_rate, spo2=data.spo2,
        supplemental_o2=data.supplemental_o2, systolic_bp=data.systolic_bp, pulse=data.pulse,
        consciousness=data.consciousness, temperature=data.temperature, source=data.source,
        source_record_id=data.source_record_id, is_simulated=data.is_simulated,
        entered_by=None if is_machine else actor_id, status="VALID", payload_hash=payload_hash,
    )
    db.add(row)
    db.flush()
    assessment = persist_assessment(db, admission, now)
    db.flush()
    from app.services.alerts import apply_assessment_to_alert
    apply_assessment_to_alert(db, admission, assessment, now, actor_id, getattr(request.state, "request_id", None))
    _audit(db, request, actor_id, "observation.accepted", "observation", row.id)
    _audit(db, request, actor_id, "assessment.computed", "risk_assessment", assessment.id)
    db.commit()
    db.refresh(row)
    return row, False, plausibility_warnings(data)


def admission_payload(db: DBSession, admission: Admission) -> dict:
    patient = db.get(Patient, admission.patient_id)
    ward = db.get(Ward, admission.ward_id)
    return {
        "id": admission.id, "patient_id": patient.id, "patient_identifier": patient.patient_identifier,
        "age_years": patient.age_years, "sex": patient.sex, "ward_id": ward.id,
        "ward_name": ward.name, "bed_label": admission.bed_label,
        "admitted_at": admission.admitted_at, "discharged_at": admission.discharged_at,
        "spo2_scale": admission.spo2_scale, "status": admission.status,
    }
