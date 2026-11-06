from collections import defaultdict
from datetime import datetime, timezone
from statistics import median

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.auth import current_session
from app.core.db import get_db
from app.models.base import Admission, Alert, AppUser, ClinicalResponse, DataSourceStatus, Escalation, IngestionRejection, LabResult, ModelPrediction, RiskAssessment
from app.services.clinical import _audit, _visible_ward_ids
from app.services.model_registry import InvalidModelArtifact, load_verified_active, verified_evaluation

router = APIRouter(prefix="/api/v1", tags=["analytics-and-labs"])


def _scope(db: DBSession, user: AppUser):
    query = select(Admission)
    wards = _visible_ward_ids(db, user)
    return query.where(Admission.ward_id.in_(wards)) if wards is not None and wards else (query.where(Admission.id == "") if wards == set() else query)


def _percentile(values: list[float], fraction: float):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low, high = int(position), min(int(position) + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (position - low), 2)


@router.get("/analytics")
def analytics(request: Request, user: AppUser = Depends(current_session), db: DBSession = Depends(get_db)):
    admissions = db.scalars(_scope(db, user)).all()
    admission_ids = [item.id for item in admissions]
    now = getattr(request.app.state, "clock", None)
    now = now.now() if now else datetime.now(timezone.utc)
    alerts = db.scalars(select(Alert).where(Alert.admission_id.in_(admission_ids))).all() if admission_ids else []
    escalations = db.scalars(select(Escalation).where(Escalation.alert_id.in_([row.id for row in alerts]))).all() if alerts else []
    responses = db.scalars(select(ClinicalResponse).where(ClinicalResponse.alert_id.in_([row.id for row in alerts]))).all() if alerts else []
    latest: dict[str, RiskAssessment] = {}
    assessments = db.scalars(select(RiskAssessment).where(RiskAssessment.admission_id.in_(admission_ids)).order_by(RiskAssessment.computed_at)).all() if admission_ids else []
    for row in assessments:
        latest[row.admission_id] = row
    duration_hours = sum(max(0.0, ((item.discharged_at or now) - item.admitted_at).total_seconds() / 3600) for item in admissions)
    ack_minutes = [(row.acknowledged_at - row.created_at).total_seconds() / 60 for row in alerts if row.acknowledged_at]
    level_counts = defaultdict(int)
    for row in alerts:
        level_counts[row.level] += 1
    denominator = len(alerts)
    operational = {
        "alerts_by_level": dict(level_counts), "alerts_total": denominator,
        "acknowledgement_median_minutes": round(median(ack_minutes), 2) if ack_minutes else None,
        "acknowledgement_p90_minutes": _percentile(ack_minutes, .9),
        "escalation_rate": round(len(escalations) / denominator, 4) if denominator else None,
        "alerts_per_patient_day": round(denominator / (duration_hours / 24), 4) if duration_hours else None,
        "data_completeness_rate": round(sum(row.completeness for row in latest.values()) / (7 * len(latest)), 4) if latest else None,
        "assessed_admissions": len(latest), "response_records": len(responses),
    }
    by_scenario: dict[str, list[Admission]] = defaultdict(list)
    for admission in admissions:
        if admission.simulation_scenario:
            by_scenario[admission.simulation_scenario].append(admission)
    scenario_rows = []
    for scenario, group in sorted(by_scenario.items()):
        ids = [item.id for item in group]
        scenario_alerts = [row for row in alerts if row.admission_id in ids]
        rejected = db.scalar(select(func.count()).select_from(IngestionRejection).where(IngestionRejection.admission_id.in_(ids))) or 0
        ward_ids = [item.ward_id for item in group]
        source_rows = db.scalars(select(DataSourceStatus).where(
            DataSourceStatus.source.like(f"sim-{scenario}-%"), DataSourceStatus.ward_id.in_(ward_ids),
        )).all()
        scenario_rows.append({
            "scenario": scenario, "admissions": len(group), "alerts_recorded": len(scenario_alerts),
            "incomplete_or_stale": sum(1 for item in ids if latest.get(item) and latest[item].level in ("INCOMPLETE", "STALE")),
            "rejected_records": rejected, "disconnected_sources": sum(1 for row in source_rows if not row.connected),
        })
    try:
        model = verified_evaluation()
        model_state = "deployed" if model else "none"
    except InvalidModelArtifact:
        model, model_state = None, "invalid"
    _audit(db, request, user.id, "analytics.read", "analytics", None)
    db.commit()
    return {
        "generated_at": now, "source": "Application database at request time",
        "operational": operational, "scenario_outcomes": scenario_rows,
        "model_state": model_state, "model_evaluation": model,
    }


@router.get("/admissions/{admission_id}/labs")
def labs(admission_id: str, request: Request, limit: int = Query(100, ge=1, le=500), user: AppUser = Depends(current_session), db: DBSession = Depends(get_db)):
    admission = db.scalar(_scope(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    rows = db.scalars(select(LabResult).where(LabResult.admission_id == admission.id).order_by(LabResult.measured_at.desc()).limit(limit)).all()
    _audit(db, request, user.id, "lab_result.list", "admission", admission.id)
    db.commit()
    return {"items": [{"id": row.id, "test_code": row.test_code, "value": row.value, "unit": row.unit,
                       "measured_at": row.measured_at, "is_simulated": row.is_simulated} for row in rows]}


@router.get("/admissions/{admission_id}/model-predictions")
def model_predictions(admission_id: str, request: Request, user: AppUser = Depends(current_session), db: DBSession = Depends(get_db)):
    admission = db.scalar(_scope(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    assessments = db.scalars(select(RiskAssessment).where(RiskAssessment.admission_id == admission.id)).all()
    try:
        active = load_verified_active()
    except InvalidModelArtifact:
        active = None
    if active:
        from app.services.model_registry import persist_prediction
        for assessment in assessments:
            try:
                persist_prediction(db, admission, assessment)
            except Exception:
                db.rollback()
                break
    rows = []
    if active:
        manifest = active["manifest"]
        rows = db.scalars(select(ModelPrediction).join(RiskAssessment).where(
            RiskAssessment.admission_id == admission.id,
            ModelPrediction.model_id == manifest["model_id"], ModelPrediction.model_version == manifest["version"],
        ).order_by(RiskAssessment.computed_at.desc()).limit(10)).all()
    _audit(db, request, user.id, "model_prediction.list", "admission", admission.id)
    db.commit()
    return {"items": [{"model_id": row.model_id, "model_version": row.model_version, "probability": float(row.probability),
                       "calibrated": row.calibrated, "explanation": row.explanation, "interface_demo": row.interface_demo} for row in rows]}
