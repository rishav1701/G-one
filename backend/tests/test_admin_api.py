import secrets
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.api.auth import digest
from app.core.db import SessionLocal
from app.domain.clock import SystemClock
from app.main import app
from app.models.base import AppUser, Role, Session, Ward, UserWard


@pytest.fixture
def admin_client():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    ward = Ward(name=f"Admin test {suffix}")
    admin = AppUser(username=f"admin-{suffix}", password_hash="unused", role=Role.ADMIN, active=True)
    viewer = AppUser(username=f"viewer-{suffix}", password_hash="unused", role=Role.VIEWER, active=True)
    db.add_all([ward, admin, viewer]); db.flush()
    db.add(UserWard(user_id=viewer.id, ward_id=ward.id))
    credentials = {}
    for user in (admin, viewer):
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.add(Session(token_hash=digest(raw), csrf_hash=digest(csrf), user_id=user.id, created_at=now, last_seen_at=now, expires_at=now+timedelta(hours=2)))
        credentials[user.role.value] = (raw, csrf)
    db.commit()
    client = TestClient(app)
    yield client, credentials, ward.id
    client.close()
    app.state.clock = SystemClock()
    db = SessionLocal()
    db.query(Session).filter(Session.user_id.in_([admin.id, viewer.id])).delete(synchronize_session=False)
    db.query(UserWard).filter(UserWard.user_id.in_([admin.id, viewer.id])).delete(synchronize_session=False)
    db.delete(admin); db.delete(viewer); db.delete(ward); db.commit(); db.close()


def auth(client, credentials, role):
    raw, csrf = credentials[role]
    client.cookies.set("g_one_session", raw)
    client.cookies.set("g_one_csrf", csrf)
    return {"X-CSRF-Token": csrf}


def test_admin_users_status_and_audit_are_admin_only(admin_client):
    client, credentials, ward_id = admin_client
    admin_headers = auth(client, credentials, "ADMIN")
    assert client.get("/api/v1/admin/users").status_code == 200
    denied = TestClient(app)
    viewer_headers = auth(denied, credentials, "VIEWER")
    assert denied.get("/api/v1/admin/users").status_code == 403
    username = "phase5-clinician-"+uuid.uuid4().hex[:8]
    created = client.post("/api/v1/admin/users", headers=admin_headers, json={"username":username,"password":"a-long-test-password","role":"SENIOR_CLINICIAN","ward_ids":[ward_id]})
    assert created.status_code == 201, created.text
    assert "password_hash" not in created.json()
    assert created.json()["ward_ids"] == [ward_id]
    assert client.get("/api/v1/admin/status").json()["database"] == "connected"
    audit = client.get("/api/v1/admin/audit?limit=20")
    assert audit.status_code == 200 and audit.json()["total"] >= 1
    assert any(row["action"] == "admin.user_created" for row in audit.json()["items"])
    cleanup = SessionLocal()
    made = cleanup.query(AppUser).filter_by(username=username).first()
    cleanup.query(UserWard).filter_by(user_id=made.id).delete(synchronize_session=False)
    cleanup.delete(made); cleanup.commit(); cleanup.close()
    assert denied.post("/api/v1/admin/simulator/reset", headers=viewer_headers, json={"seed":42}).status_code == 403
def test_admin_can_reset_deterministic_simulator(admin_client):
    client, credentials, _ = admin_client
    headers = auth(client, credentials, "ADMIN")
    result = client.post("/api/v1/admin/simulator/reset", headers=headers, json={"seed":42})
    assert result.status_code == 200, result.text
    assert result.json()["patients"] == 12
    assert result.json()["scenarios"] == ["stable", "gradual_deterioration", "sudden_concerning_change", "missing_observations", "sensor_disconnection", "data_quality_problems"]
    admissions = client.get("/api/v1/admissions?limit=200").json()["items"]
    missing = next(row for row in admissions if row["patient_identifier"] == "SIM-000007")
    assessments = client.get(f"/api/v1/admissions/{missing['id']}/assessments?limit=1").json()
    assert assessments[0]["level"] == "INCOMPLETE"
    advance = client.post("/api/v1/admin/simulator/advance", headers=headers, json={"minutes":5})
    assert advance.status_code == 200
    refreshed = client.get(f"/api/v1/admissions/{missing['id']}/assessments?limit=1").json()
    assert refreshed[0]["level"] == "STALE"