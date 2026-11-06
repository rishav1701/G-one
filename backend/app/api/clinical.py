from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as DBSession

from app.api.auth import current_session
from app.core.db import get_db
from app.domain.clock import SystemClock
from app.domain.news2 import PARAMETERS, SpO2Scale, calculate_news2
from app.models.base import Admission, AppUser, AuditLog, Observation, Patient, RiskAssessment, Role, UserWard
from app.schemas.clinical import AdmissionResponse, ObservationResponse, PageResponse, PatientPageResponse, PatientResponse, RiskAssessmentResponse
from app.services.clinical import _audit, _visible_ward_ids, admission_payload, record_observation, refresh_current_assessment

router = APIRouter(prefix="/api/v1", tags=["clinical"])


def ingestion_auth(request: Request, db: DBSession = Depends(get_db)):
    """Route-enumeration marker; record_observation enforces the credential and role."""
    if request.headers.get("X-API-Key"):
        return
    user = current_session(request, db)
    if user.role not in (Role.CLINICIAN, Role.SENIOR_CLINICIAN):
        raise HTTPException(status_code=403, detail="Access denied")


def _scoped_admissions(db: DBSession, user: AppUser):
    query = select(Admission)
    ward_ids = _visible_ward_ids(db, user)
    if ward_ids is not None:
        if not ward_ids:
            return query.where(Admission.id == "")
        query = query.where(Admission.ward_id.in_(ward_ids))
    return query


@router.post("/observations", response_model=ObservationResponse, status_code=201, dependencies=[Depends(ingestion_auth)])
def submit_observation(payload: dict, request: Request, db: DBSession = Depends(get_db)):
    row, replay, warnings = record_observation(db, request, payload, getattr(request.app.state, "clock", None))
    return {
        "id": row.id, "admission_id": row.admission_id, "measured_at": row.measured_at,
        "received_at": row.received_at, "status": row.status,
        "idempotent_replay": replay, "plausibility_warnings": warnings,
    }


@router.get("/admissions", response_model=PageResponse)
def list_admissions(
    request: Request,
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    status: str | None = Query(None, pattern="^(ACTIVE|DISCHARGED)$"),
    ward_id: str | None = None, q: str | None = Query(None, max_length=80),
    sort: str = Query("admitted_at", pattern="^(admitted_at|bed_label|patient_identifier)$"),
    direction: str = Query("desc", pattern="^(asc|desc)$"),
    user: AppUser = Depends(current_session), db: DBSession = Depends(get_db),
):
    query = _scoped_admissions(db, user).join(Patient, Patient.id == Admission.patient_id)
    if status:
        query = query.where(Admission.status == status)
    if ward_id:
        query = query.where(Admission.ward_id == ward_id)
    if q:
        query = query.where(or_(Patient.patient_identifier.ilike(f"%{q}%"), Admission.bed_label.ilike(f"%{q}%")))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    sort_column = {
        "admitted_at": Admission.admitted_at,
        "bed_label": Admission.bed_label,
        "patient_identifier": Patient.patient_identifier,
    }[sort]
    query = query.order_by(sort_column.asc() if direction == "asc" else sort_column.desc(), Admission.id)
    admissions = db.scalars(query.limit(limit).offset(offset)).all()
    for admission in admissions:
        _audit(db, request, user.id, "admission.read", "admission", admission.id)
    db.commit()
    return {"items": [admission_payload(db, admission) for admission in admissions], "limit": limit, "offset": offset, "total": total}


@router.get("/admissions/{admission_id}", response_model=AdmissionResponse)
def get_admission(admission_id: str, request: Request, user: AppUser = Depends(current_session), db: DBSession = Depends(get_db)):
    admission = db.scalar(_scoped_admissions(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    _audit(db, request, user.id, "admission.read", "admission", admission.id)
    db.commit()
    return admission_payload(db, admission)


@router.get("/patients", response_model=PatientPageResponse)
def list_patients(
    request: Request,
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=80),
    user: AppUser = Depends(current_session), db: DBSession = Depends(get_db),
):
    query = select(Patient).join(Admission, Admission.patient_id == Patient.id)
    ward_ids = _visible_ward_ids(db, user)
    if ward_ids is not None:
        if not ward_ids:
            return {"items": [], "limit": limit, "offset": offset, "total": 0}
        query = query.where(Admission.ward_id.in_(ward_ids))
    if q:
        query = query.where(Patient.patient_identifier.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(query.with_only_columns(Patient.id).distinct().subquery())) or 0
    patients = db.scalars(query.distinct().order_by(Patient.patient_identifier).limit(limit).offset(offset)).all()
    for patient in patients:
        _audit(db, request, user.id, "patient.read", "patient", patient.id)
    db.commit()
    return {"items": patients, "limit": limit, "offset": offset, "total": total}


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, request: Request, user: AppUser = Depends(current_session), db: DBSession = Depends(get_db)):
    visible = _scoped_admissions(db, user).where(Admission.patient_id == patient_id).limit(1)
    admission = db.scalar(visible)
    if admission is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient = db.get(Patient, patient_id)
    _audit(db, request, user.id, "patient.read", "patient", patient.id)
    db.commit()
    return patient


@router.get("/admissions/{admission_id}/observations", response_model=list[ObservationResponse])
def list_observations(
    admission_id: str, request: Request,
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    user: AppUser = Depends(current_session), db: DBSession = Depends(get_db),
):
    admission = db.scalar(_scoped_admissions(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    rows = db.scalars(select(Observation).where(Observation.admission_id == admission_id).order_by(Observation.measured_at.desc()).limit(limit).offset(offset)).all()
    _audit(db, request, user.id, "observation.list", "admission", admission_id)
    db.commit()
    return rows


@router.get("/admissions/{admission_id}/monitoring")
def list_monitoring_points(
    admission_id: str, request: Request,
    limit: int = Query(500, ge=1, le=1000), offset: int = Query(0, ge=0),
    user: AppUser = Depends(current_session), db: DBSession = Depends(get_db),
):
    admission = db.scalar(_scoped_admissions(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    rows = db.scalars(select(Observation).where(
        Observation.admission_id == admission_id, Observation.status == "VALID",
    ).order_by(Observation.measured_at.desc()).limit(limit).offset(offset)).all()
    points = []
    for row in rows:
        values = {name: getattr(row, name) for name in PARAMETERS}
        score = calculate_news2(values, spo2_scale=SpO2Scale(admission.spo2_scale))
        points.append({
            "id": row.id, "measured_at": row.measured_at, "values": values,
            "parameter_scores": score.scores, "total": score.total,
        })
    _audit(db, request, user.id, "monitoring.read", "admission", admission_id)
    db.commit()
    return {"items": list(reversed(points)), "limit": limit, "offset": offset}


@router.get("/admissions/{admission_id}/assessments", response_model=list[RiskAssessmentResponse])
def list_assessments(
    admission_id: str, request: Request,
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    user: AppUser = Depends(current_session), db: DBSession = Depends(get_db),
):
    admission = db.scalar(_scoped_admissions(db, user).where(Admission.id == admission_id))
    if admission is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    clock = getattr(request.app.state, "clock", SystemClock())
    now = clock.now()
    # Persisted simulator assessments represent deterministic scenario steps. Keep their
    # expected states visible until an explicit simulated-clock action recomputes them.
    if not admission.is_simulated or getattr(clock, "refresh_assessments", False):
        refresh_current_assessment(db, admission, now, request.state.request_id)
    rows = db.scalars(select(RiskAssessment).where(RiskAssessment.admission_id == admission_id).order_by(RiskAssessment.computed_at.desc()).limit(limit).offset(offset)).all()
    _audit(db, request, user.id, "assessment.list", "admission", admission_id)
    db.commit()
    return rows
