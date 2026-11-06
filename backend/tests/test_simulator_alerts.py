from datetime import datetime, timedelta, timezone
import secrets

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError

from app.api.auth import digest
from app.core.db import SessionLocal
from app.domain.news2 import Level
from app.models.base import (
    Admission, Alert, AlertEvent, AppUser, AuditLog, ClinicalResponse,
    DataSourceStatus, Escalation, Observation, RiskAssessment, Role, Session,
    SystemConfig, UserWard,
)
from fastapi.testclient import TestClient
from app.main import app
from app.services.alerts import (
    acknowledge_alert, apply_assessment_to_alert, ensure_escalations,
    record_response, resolve_alert,
)
from simulator.engine import START, reset_simulation, run_seed


def test_scenario_outcomes_are_deterministic_and_duplicate_safe():
    db = SessionLocal()
    try:
        first = run_seed(db, 731)
        second = run_seed(db, 731)
        assert first["output_sha256"] == second["output_sha256"]
        assert first["patients"] == 12 and first["wards"] == 2
        stable = [event for event in first["events"] if event["scenario"] == "stable"]
        assert all(event["level"] == Level.LOW.value and event["alert_level"] is None for event in stable)
        gradual = [event for event in first["events"] if event["scenario"] == "gradual_deterioration"]
        assert all(event["alert_level"] is None for event in gradual if event["step"] < 2)
        assert all(event["alert_level"] == Level.LOW_MEDIUM.value for event in gradual if event["step"] == 2)
        sudden = [event for event in first["events"] if event["scenario"] == "sudden_concerning_change"]
        assert all(event["alert_level"] == Level.HIGH.value for event in sudden if event["step"] == 1)
        missing = [event for event in first["events"] if event["scenario"] == "missing_observations"]
        assert all(event["level"] == Level.INCOMPLETE.value and event["level"] != Level.LOW.value for event in missing)
        disconnected = [event for event in first["events"] if event["step"] == "disconnected"]
        assert len(disconnected) == 2 and all(event["level"] == Level.STALE.value for event in disconnected)
        quality = [event for event in first["events"] if event["step"] == "data_quality"]
        assert len(quality) == 2 and all(event["duplicate_replay"] and event["conflict_rejected"] and event["hard_range_rejected"] and event["out_of_order_accepted"] for event in quality)
        scenario_admission_ids = list(db.scalars(select(Admission.id).where(Admission.simulation_scenario == "data_quality_problems")).all())
        for admission_id in scenario_admission_ids:
            rows = list(db.scalars(select(Observation).where(Observation.admission_id == admission_id)).all())
            assert len(rows) == 2
        statuses = db.query(DataSourceStatus).filter(DataSourceStatus.source.like("sim-sensor_disconnection-%")).all()
        assert len(statuses) == 2 and all(not status.connected and status.is_simulated for status in statuses)
    finally:
        reset_simulation(db)
        db.close()


def _assessment(db, admission_id, level, now, number):
    result = RiskAssessment(
        admission_id=admission_id, scoring_version="NEWS2-RCP-2017-v1", spo2_scale=1,
        observation_ids=[], per_parameter_scores={}, completeness=7 if level != "INCOMPLETE" else 1,
        level=level, total=7 if level == "HIGH" else 5 if level == "MEDIUM" else 0,
        explanation={"scoring_version": "NEWS2-RCP-2017-v1", "scores": {}, "completeness": 7,
                    "total": 7 if level == "HIGH" else 5 if level == "MEDIUM" else 0,
                    "level": level, "partial": False, "lower_bound": False},
        computed_at=now,
    )
    db.add(result)
    db.flush()
    return result


def test_alert_hysteresis_escalation_resolution_and_audit_append_only():
    db = SessionLocal()
    try:
        run_seed(db, 732)
        admission = db.scalar(select(Admission).where(Admission.simulation_scenario == "gradual_deterioration").limit(1))
        alert = db.scalar(select(Alert).where(Alert.admission_id == admission.id))
        assert alert.status == "OPEN" and alert.level == "LOW_MEDIUM"
        original_alert_id = alert.id
        actor = db.scalar(select(AppUser).where(AppUser.role == Role.SENIOR_CLINICIAN).limit(1))
        if actor is None:
            actor = AppUser(username="phase3-senior", password_hash="unused", role=Role.SENIOR_CLINICIAN, active=True)
            db.add(actor)
            db.flush()
        now = START + timedelta(hours=1)
        for index, level in enumerate(("HIGH", "MEDIUM", "MEDIUM", "LOW", "LOW")):
            result = _assessment(db, admission.id, level, now + timedelta(minutes=index), index)
            alert = apply_assessment_to_alert(db, admission, result, result.computed_at, actor.id)
            db.flush()
            if index == 0:
                assert alert.level == "HIGH" and alert.id == original_alert_id
            if index == 1:
                assert alert.level == "HIGH" and alert.consecutive_lower == 1
            if index == 2:
                assert alert.level == "MEDIUM"
            if index == 3:
                assert alert.status == "OPEN" and alert.score_returned_to_low
            if index == 4:
                assert alert.status == "OPEN" and alert.score_returned_to_low
        count = db.query(Alert).filter_by(admission_id=admission.id, status="OPEN").count()
        assert count == 1

        acknowledged = acknowledge_alert(db, alert, actor, now + timedelta(minutes=10))
        assert acknowledged.status == "ACKNOWLEDGED"
        risen = _assessment(db, admission.id, "HIGH", now + timedelta(minutes=10, seconds=1), 99)
        updated = apply_assessment_to_alert(db, admission, risen, risen.computed_at, actor.id)
        assert updated.id == original_alert_id and updated.status == "ACKNOWLEDGED"
        assert db.query(Alert).filter_by(admission_id=admission.id, status="ACKNOWLEDGED").count() == 1
        response = record_response(db, acknowledged, actor, now + timedelta(minutes=11), "LOCAL_ESCALATION", "SENIOR_CLINICIAN", "Reviewed under local policy")
        assert response.action == "LOCAL_ESCALATION"
        resolve_alert(db, acknowledged, actor, now + timedelta(minutes=12))
        assert acknowledged.status == "RESOLVED"
        no_duplicate = _assessment(db, admission.id, "HIGH", now + timedelta(minutes=13), 100)
        assert apply_assessment_to_alert(db, admission, no_duplicate, no_duplicate.computed_at, actor.id) is None

        sudden = db.scalar(select(Admission).where(Admission.simulation_scenario == "sudden_concerning_change").limit(1))
        sudden_alert = db.scalar(select(Alert).where(Alert.admission_id == sudden.id))
        for open_alert in db.scalars(select(Alert).where(Alert.status == "OPEN")).all():
            open_alert.created_at = now
        sudden_alert.created_at = now - timedelta(minutes=10)
        db.flush()
        assert sudden_alert.status == "OPEN"
        assert sudden_alert.created_at <= now - timedelta(minutes=5)
        db.query(Escalation).filter_by(alert_id=sudden_alert.id).delete(synchronize_session=False)
        assert ensure_escalations(db, now) == 1
        assert ensure_escalations(db, now) == 0
        assert db.query(Escalation).filter_by(alert_id=sudden_alert.id).count() == 1

        audit = db.scalar(select(AuditLog).limit(1))
        assert audit is not None
        with pytest.raises(DBAPIError, match="audit_log is append-only"):
            db.execute(update(AuditLog).where(AuditLog.id == audit.id).values(action="tampered"))
            db.flush()
        db.rollback()
        with pytest.raises(DBAPIError, match="audit_log is append-only"):
            db.execute(delete(AuditLog).where(AuditLog.id == audit.id))
            db.flush()
        db.rollback()
    finally:
        db.rollback()
        reset_simulation(db)
        db.query(AppUser).filter_by(username="phase3-senior").delete(synchronize_session=False)
        db.commit()
        db.close()


def _client_for(user):
    client = TestClient(app)
    client.cookies.set("g_one_session", user.session_token)
    client.cookies.set("g_one_csrf", user.session_csrf)
    return client


def test_alert_and_operational_settings_routes_enforce_roles_and_scope():
    db = SessionLocal()
    users = []
    try:
        run_seed(db, 733)
        admission = db.scalar(select(Admission).where(Admission.simulation_scenario == "gradual_deterioration").limit(1))
        now = START + timedelta(hours=1)
        for role, suffix, ward_id in ((Role.ADMIN, "admin", None), (Role.SENIOR_CLINICIAN, "senior", admission.ward_id),
                                     (Role.CLINICIAN, "clinician", admission.ward_id), (Role.VIEWER, "viewer", admission.ward_id),
                                     (Role.VIEWER, "outsider", None)):
            user = AppUser(username=f"phase3-{suffix}", password_hash="unused", role=role, active=True)
            db.add(user)
            db.flush()
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            auth_now = datetime.now(timezone.utc)
            db.add(Session(token_hash=digest(token), csrf_hash=digest(csrf), user_id=user.id,
                           created_at=auth_now, last_seen_at=auth_now, expires_at=auth_now+timedelta(hours=2)))
            user.session_token, user.session_csrf = token, csrf
            if ward_id:
                db.add(UserWard(user_id=user.id, ward_id=ward_id))
            users.append(user)
        db.commit()
        admin, senior, clinician, viewer, outsider = users

        viewer_client = _client_for(viewer)
        assert viewer_client.get("/api/v1/settings/operational").status_code == 200
        assert db.query(AuditLog).filter_by(actor_id=viewer.id, action="system_config.read").count() == 1
        forbidden = viewer_client.put("/api/v1/settings/operational", json={"minimum_alert_level": "MEDIUM"}, headers={"X-CSRF-Token": viewer.session_csrf})
        assert forbidden.status_code == 403
        admin_client = _client_for(admin)
        updated = admin_client.put("/api/v1/settings/operational", json={
            "minimum_alert_level": "LOW_MEDIUM", "alert_downgrade_assessments": "2",
            "alert_escalation_delay_minutes": "1440", "alert_escalation_check_seconds": "10",
        }, headers={"X-CSRF-Token": admin.session_csrf})
        assert updated.status_code == 200
        assert db.query(AuditLog).filter_by(actor_id=admin.id, action="system_config.updated").count() == 4

        clinician_client = _client_for(clinician)
        alerts = clinician_client.get("/api/v1/alerts?status=OPEN")
        assert alerts.status_code == 200 and alerts.json()["total"] >= 1
        alert_id = next(item["id"] for item in alerts.json()["items"] if item["admission_id"] == admission.id)
        detail = clinician_client.get(f"/api/v1/alerts/{alert_id}")
        assert detail.status_code == 200
        assert detail.json()["policy_text"] == "Follow local escalation policy"
        assert detail.json()["events"][0]["event_type"] == "CREATED"
        assert _client_for(outsider).get(f"/api/v1/alerts/{alert_id}").status_code == 404

        viewer_ack = viewer_client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers={"X-CSRF-Token": viewer.session_csrf})
        assert viewer_ack.status_code == 403
        ack = clinician_client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers={"X-CSRF-Token": clinician.session_csrf})
        assert ack.status_code == 200 and ack.json()["status"] == "ACKNOWLEDGED"
        replay_ack = clinician_client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers={"X-CSRF-Token": clinician.session_csrf})
        assert replay_ack.status_code == 200
        response = clinician_client.post(f"/api/v1/alerts/{alert_id}/responses", json={
            "assessed_at": now.isoformat(), "action": "CLINICAL_REVIEW",
            "escalated_to_role": "SENIOR_CLINICIAN", "notes": "Reviewed; identifiers omitted.",
        }, headers={"X-CSRF-Token": clinician.session_csrf})
        assert response.status_code == 200 and "Do not enter patient identifiers" in response.json()["warning"]
        long_notes = clinician_client.post(f"/api/v1/alerts/{alert_id}/responses", json={"assessed_at": now.isoformat(), "action": "OTHER", "notes": "x" * 501}, headers={"X-CSRF-Token": clinician.session_csrf})
        assert long_notes.status_code == 422
        assert clinician_client.post(f"/api/v1/alerts/{alert_id}/resolve", headers={"X-CSRF-Token": clinician.session_csrf}).status_code == 403
        resolved = _client_for(senior).post(f"/api/v1/alerts/{alert_id}/resolve", headers={"X-CSRF-Token": senior.session_csrf})
        assert resolved.status_code == 200 and resolved.json()["status"] == "RESOLVED"
    finally:
        db.rollback()
        reset_simulation(db)
        db.query(Session).filter(Session.user_id.in_([user.id for user in users])).delete(synchronize_session=False)
        db.query(UserWard).filter(UserWard.user_id.in_([user.id for user in users])).delete(synchronize_session=False)
        db.query(AppUser).filter(AppUser.username.in_([user.username for user in users])).delete(synchronize_session=False)
        db.commit()
        db.close()
