import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.domain.news2 import Level
from app.models.base import (
    Admission, Alert, AlertEvent, AppUser, AuditLog, ClinicalResponse,
    Escalation, RiskAssessment, SystemConfig,
)

LEVEL_RANK = {Level.NO_DATA.value: 0, Level.STALE.value: 0, Level.INCOMPLETE.value: 0,
              Level.LOW.value: 0, Level.LOW_MEDIUM.value: 1, Level.MEDIUM.value: 2, Level.HIGH.value: 3}
ALERT_LEVELS = {"LOW_MEDIUM", "MEDIUM", "HIGH"}
DEFAULTS = {
    "minimum_alert_level": "LOW_MEDIUM",
    "alert_downgrade_assessments": "2",
    "alert_escalation_delay_minutes": "5",
    "alert_escalation_check_seconds": "10",
}


def setting(db: DBSession, key: str) -> str:
    record = db.get(SystemConfig, key)
    return record.value if record else DEFAULTS[key]


def settings_view(db: DBSession) -> dict[str, str]:
    return {key: setting(db, key) for key in DEFAULTS}


def update_settings(db: DBSession, actor: AppUser, request_id: str, changes: dict[str, str], now):
    if not changes or set(changes) - set(DEFAULTS):
        raise ValueError("Unsupported operational setting")
    merged = settings_view(db) | changes
    if merged["minimum_alert_level"] not in ALERT_LEVELS:
        raise ValueError("Invalid minimum alert level")
    for name, minimum, maximum in (("alert_downgrade_assessments", 1, 10), ("alert_escalation_delay_minutes", 1, 1440), ("alert_escalation_check_seconds", 1, 300)):
        value = int(merged[name])
        if not minimum <= value <= maximum:
            raise ValueError("Operational setting is outside its allowed range")
    for key, value in changes.items():
        row = db.get(SystemConfig, key)
        if row is None:
            db.add(SystemConfig(key=key, value=str(value)))
        else:
            row.value = str(value)
        db.add(AuditLog(actor_id=actor.id, action="system_config.updated", object_type="system_config", object_id=None, request_id=request_id, created_at=now))


def _event(db: DBSession, alert: Alert, event_type: str, now, *, actor_id: str | None = None, from_level: str | None = None, to_level: str | None = None, code: str | None = None, request_id: str | None = None):
    db.add(AlertEvent(alert_id=alert.id, event_type=event_type, actor_id=actor_id, from_level=from_level, to_level=to_level, detail_code=code, created_at=now))
    db.add(AuditLog(actor_id=actor_id, action=f"alert.{event_type.lower()}", object_type="alert", object_id=alert.id, request_id=request_id or str(uuid.uuid4()), created_at=now))


def apply_assessment_to_alert(db: DBSession, admission: Admission, assessment: RiskAssessment, now, actor_id: str | None = None, request_id: str | None = None) -> Alert | None:
    level = assessment.level
    threshold = setting(db, "minimum_alert_level")
    rank = LEVEL_RANK[level]
    threshold_rank = LEVEL_RANK[threshold]
    active = db.scalar(select(Alert).where(Alert.admission_id == admission.id, Alert.status.in_(("OPEN", "ACKNOWLEDGED"))).with_for_update())
    if active is None:
        previous = db.scalar(select(Alert).where(Alert.admission_id == admission.id).order_by(Alert.created_at.desc()).limit(1).with_for_update())
        previous_rank = LEVEL_RANK[previous.last_score_level] if previous else 0
        if previous is not None:
            previous.last_score_level = level
        if rank < threshold_rank or (previous is not None and rank <= previous_rank):
            return None
        alert = Alert(
            id=(str(uuid.uuid5(uuid.NAMESPACE_URL, "gone-alert:" + assessment.id)) if assessment.observation_ids else str(uuid.uuid4())), admission_id=admission.id, status="OPEN", level=level,
            latest_assessment_id=assessment.id, created_at=now,
            consecutive_lower=0, score_returned_to_low=False, last_score_level=level,
        )
        db.add(alert)
        db.flush()
        _event(db, alert, "CREATED", now, actor_id=actor_id, to_level=level, request_id=request_id)
        return alert
    old_level = active.level
    active.latest_assessment_id = assessment.id
    active.last_score_level = level
    if rank > LEVEL_RANK[old_level]:
        active.level = level
        active.consecutive_lower = 0
        active.score_returned_to_low = False
        _event(db, active, "LEVEL_RAISED", now, actor_id=actor_id, from_level=old_level, to_level=level, request_id=request_id)
    elif rank < LEVEL_RANK[old_level]:
        active.consecutive_lower += 1
        if level == Level.LOW.value:
            if not active.score_returned_to_low:
                active.score_returned_to_low = True
                _event(db, active, "SCORE_RETURNED_TO_LOW", now, actor_id=actor_id, from_level=old_level, code="AWAITING_CLINICAL_RESOLUTION", request_id=request_id)
        elif active.consecutive_lower >= int(setting(db, "alert_downgrade_assessments")):
            if rank > 0:
                active.level = level
                active.consecutive_lower = 0
                active.score_returned_to_low = False
                _event(db, active, "LEVEL_DOWNGRADED", now, actor_id=actor_id, from_level=old_level, to_level=level, request_id=request_id)
    else:
        active.consecutive_lower = 0
    return active


def acknowledge_alert(db: DBSession, alert: Alert, actor: AppUser, now):
    if alert.status == "ACKNOWLEDGED":
        return alert
    if alert.status != "OPEN":
        raise ValueError("Only open alerts can be acknowledged")
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = now
    alert.acknowledged_by = actor.id
    _event(db, alert, "ACKNOWLEDGED", now, actor_id=actor.id)
    return alert


def record_response(db: DBSession, alert: Alert, actor: AppUser, now, action: str, escalated_to_role: str | None, notes: str | None):
    if alert.status == "RESOLVED":
        raise ValueError("Resolved alerts do not accept responses")
    response = ClinicalResponse(
        alert_id=alert.id, actor_id=actor.id, assessed_at=now, action=action,
        escalated_to_role=escalated_to_role, notes=notes,
    )
    db.add(response)
    _event(db, alert, "RESPONSE_RECORDED", now, actor_id=actor.id, code=action)
    return response


def resolve_alert(db: DBSession, alert: Alert, actor: AppUser, now):
    if alert.status == "RESOLVED":
        return alert
    alert.status = "RESOLVED"
    alert.resolved_at = now
    alert.resolved_by = actor.id
    _event(db, alert, "RESOLVED", now, actor_id=actor.id)
    return alert


def ensure_escalations(db: DBSession, now) -> int:
    delay = timedelta(minutes=int(setting(db, "alert_escalation_delay_minutes")))
    alerts = db.scalars(select(Alert).where(Alert.status == "OPEN", Alert.created_at <= now - delay).with_for_update()).all()
    created = 0
    for alert in alerts:
        if db.scalar(select(Escalation.id).where(Escalation.alert_id == alert.id)):
            continue
        admission = db.get(Admission, alert.admission_id)
        escalation = Escalation(alert_id=alert.id, ward_id=admission.ward_id, target_role="SENIOR_CLINICIAN", created_at=now)
        db.add(escalation)
        db.flush()
        _event(db, alert, "ESCALATED", now, code="IN_APP_DEMONSTRATION_ESCALATION")
        created += 1
    return created
