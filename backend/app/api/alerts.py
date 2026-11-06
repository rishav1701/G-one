from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.auth import current_session, require_roles
from app.core.db import get_db
from app.domain.clock import SystemClock
from app.models.base import (
    Admission, Alert, AlertEvent, AppUser, AuditLog, ClinicalResponse, Escalation,
    Role, UserWard,
)
from app.schemas.clinical import AlertActionInput, OperationalSettingsInput
from app.services.alerts import (
    acknowledge_alert, ensure_escalations, record_response, resolve_alert,
    settings_view, update_settings,
)

router = APIRouter(prefix="/api/v1", tags=["alerts-and-settings"])
CLINICAL_READERS = (Role.ADMIN, Role.SENIOR_CLINICIAN, Role.CLINICIAN, Role.VIEWER)
CLINICAL_ACTORS = (Role.SENIOR_CLINICIAN, Role.CLINICIAN)


def _now(request: Request):
    return getattr(request.app.state, "clock", SystemClock()).now()


def _visible_alert(db: DBSession, user: AppUser, alert_id: str):
    query = select(Alert).join(Admission, Admission.id == Alert.admission_id).where(Alert.id == alert_id)
    if user.role is not Role.ADMIN:
        ward_ids = set(db.scalars(select(UserWard.ward_id).where(UserWard.user_id == user.id)).all())
        if not ward_ids:
            return None
        query = query.where(Admission.ward_id.in_(ward_ids))
    return db.scalar(query)


def _alert_payload(db: DBSession, alert: Alert):
    admission = db.get(Admission, alert.admission_id)
    from app.models.base import Patient, Ward
    patient, ward = db.get(Patient, admission.patient_id), db.get(Ward, admission.ward_id)
    events = db.scalars(select(AlertEvent).where(AlertEvent.alert_id == alert.id).order_by(AlertEvent.created_at, AlertEvent.id)).all()
    responses = db.scalars(select(ClinicalResponse).where(ClinicalResponse.alert_id == alert.id).order_by(ClinicalResponse.assessed_at, ClinicalResponse.id)).all()
    escalations = db.scalars(select(Escalation).where(Escalation.alert_id == alert.id)).all()
    return {
        "id": alert.id, "admission_id": admission.id, "patient_id": patient.id, "patient_identifier": patient.patient_identifier,
        "ward_name": ward.name, "bed_label": admission.bed_label,
        "status": alert.status, "level": alert.level,
        "created_at": alert.created_at, "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at, "score_returned_to_low": alert.score_returned_to_low,
        "note": "Score returned to low, awaiting clinical resolution" if alert.score_returned_to_low else None,
        "policy_text": "Follow local escalation policy",
        "escalations": [{"created_at": item.created_at, "target_role": item.target_role, "label": "In-app demonstration escalation; not a paging system"} for item in escalations],
        "events": [{"event_type": item.event_type, "from_level": item.from_level, "to_level": item.to_level, "detail_code": item.detail_code, "created_at": item.created_at} for item in events],
        "responses": [{"assessed_at": item.assessed_at, "action": item.action, "escalated_to_role": item.escalated_to_role, "notes": item.notes} for item in responses],
    }


@router.get("/alerts")
def list_alerts(
    request: Request,
    status: str | None = Query(None, pattern="^(OPEN|ACKNOWLEDGED|RESOLVED)$"),
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    user: AppUser = Depends(require_roles(*CLINICAL_READERS)), db: DBSession = Depends(get_db),
):
    now = _now(request)
    ensure_escalations(db, now)
    query = select(Alert).join(Admission, Admission.id == Alert.admission_id)
    if user.role is not Role.ADMIN:
        ward_ids = set(db.scalars(select(UserWard.ward_id).where(UserWard.user_id == user.id)).all())
        if not ward_ids:
            return {"items": [], "limit": limit, "offset": offset, "total": 0}
        query = query.where(Admission.ward_id.in_(ward_ids))
    if status:
        query = query.where(Alert.status == status)
    total = db.query(Alert).join(Admission, Admission.id == Alert.admission_id)
    if user.role is not Role.ADMIN:
        total = total.filter(Admission.ward_id.in_(ward_ids))
    if status:
        total = total.filter(Alert.status == status)
    count = total.count()
    alerts = db.scalars(query.order_by(Alert.created_at.desc(), Alert.id).limit(limit).offset(offset)).all()
    for alert in alerts:
        db.add(AuditLog(actor_id=user.id, action="alert.read", object_type="alert", object_id=alert.id, request_id=request.state.request_id, created_at=now))
    db.commit()
    return {"items": [_alert_payload(db, alert) for alert in alerts], "limit": limit, "offset": offset, "total": count}


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: str, request: Request, user: AppUser = Depends(require_roles(*CLINICAL_READERS)), db: DBSession = Depends(get_db)):
    now = _now(request)
    ensure_escalations(db, now)
    alert = _visible_alert(db, user, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.add(AuditLog(actor_id=user.id, action="alert.read", object_type="alert", object_id=alert.id, request_id=request.state.request_id, created_at=now))
    db.commit()
    return _alert_payload(db, alert)


@router.post("/alerts/{alert_id}/acknowledge")
def ack_alert(alert_id: str, request: Request, user: AppUser = Depends(require_roles(*CLINICAL_ACTORS)), db: DBSession = Depends(get_db)):
    now = _now(request)
    alert = _visible_alert(db, user, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        acknowledge_alert(db, alert, user, now)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.add(AuditLog(actor_id=user.id, action="alert.acknowledged", object_type="alert", object_id=alert.id, request_id=request.state.request_id, created_at=now))
    db.commit()
    return _alert_payload(db, alert)


@router.post("/alerts/{alert_id}/responses")
def respond_to_alert(alert_id: str, body: AlertActionInput, request: Request, user: AppUser = Depends(require_roles(*CLINICAL_ACTORS)), db: DBSession = Depends(get_db)):
    now = _now(request)
    if body.assessed_at > now:
        raise HTTPException(status_code=422, detail="assessed_at cannot be in the future")
    alert = _visible_alert(db, user, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        response = record_response(db, alert, user, body.assessed_at, body.action, body.escalated_to_role, body.notes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.add(AuditLog(actor_id=user.id, action="alert.response_recorded", object_type="alert", object_id=alert.id, request_id=request.state.request_id, created_at=now))
    db.commit()
    return {"id": response.id, "assessed_at": response.assessed_at, "action": response.action, "warning": "Do not enter patient identifiers in notes.", "policy_text": "Follow local escalation policy"}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert_route(alert_id: str, request: Request, user: AppUser = Depends(require_roles(Role.SENIOR_CLINICIAN)), db: DBSession = Depends(get_db)):
    now = _now(request)
    alert = _visible_alert(db, user, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    resolve_alert(db, alert, user, now)
    db.add(AuditLog(actor_id=user.id, action="alert.resolved", object_type="alert", object_id=alert.id, request_id=request.state.request_id, created_at=now))
    db.commit()
    return _alert_payload(db, alert)


@router.get("/settings/operational")
def get_operational_settings(request: Request, user: AppUser = Depends(require_roles(*CLINICAL_READERS)), db: DBSession = Depends(get_db)):
    now = _now(request)
    db.add(AuditLog(actor_id=user.id, action="system_config.read", object_type="system_config", object_id=None, request_id=request.state.request_id, created_at=now))
    db.commit()
    return settings_view(db)


@router.put("/settings/operational")
def put_operational_settings(body: OperationalSettingsInput, request: Request, user: AppUser = Depends(require_roles(Role.ADMIN)), db: DBSession = Depends(get_db)):
    try:
        changes = {key: value for key, value in body.model_dump(exclude_none=True).items()}
        update_settings(db, user, request.state.request_id, changes, _now(request))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return settings_view(db)
