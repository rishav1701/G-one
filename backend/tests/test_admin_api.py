import secrets
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.api.auth import digest, hasher
from app.core.config import settings
from app.core.demo_credentials import DEMO_ACCOUNT_PASSWORDS
from app.core.db import SessionLocal
from app.domain.clock import SystemClock
from app.main import app
from app.models.base import AppUser, AuditLog, Role, Session, Ward, UserWard
from app.seed import seed_users
from simulator.engine import reset_simulation, run_seed


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


def test_demo_seed_creates_separate_clinical_login_and_preserves_passwords():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    admin_name = f"seed-admin-{suffix}"
    clinician_name = f"seed-clinician-{suffix}"
    try:
        run_seed(db, int(suffix[:6], 16))
        first_messages = seed_users(
            db,
            admin_username=admin_name,
            admin_password="admin-test-password-1",
            clinician_username=clinician_name,
            clinician_password="clinician-test-password-1",
        )
        admin = db.query(AppUser).filter_by(username=admin_name).one()
        clinician = db.query(AppUser).filter_by(username=clinician_name).one()
        assert admin.role is Role.ADMIN
        assert not db.query(UserWard).filter_by(user_id=admin.id).first()
        assert clinician.role is Role.SENIOR_CLINICIAN
        assert {row.ward_id for row in db.query(UserWard).filter_by(user_id=clinician.id)} == {
            row.id for row in db.query(Ward).filter(Ward.name.like("Simulation Ward %"))
        }
        assert any("one-time password for ADMIN" in item for item in first_messages)
        assert any("one-time password for SENIOR_CLINICIAN" in item for item in first_messages)

        assigned_wards = {
            row.ward_id for row in db.query(UserWard).filter_by(user_id=clinician.id)
        }
        run_seed(db, int(suffix[:6], 16) + 1)
        assert {
            row.ward_id for row in db.query(UserWard).filter_by(user_id=clinician.id)
        } == assigned_wards

        admin_hash = admin.password_hash
        clinician_hash = clinician.password_hash
        second_messages = seed_users(
            db,
            admin_username=admin_name,
            admin_password="changed-admin-password-2",
            clinician_username=clinician_name,
            clinician_password="changed-clinician-password-2",
        )
        assert admin.password_hash == admin_hash
        assert clinician.password_hash == clinician_hash
        assert all("changed-" not in item for item in second_messages)

        now = datetime.now(timezone.utc)
        db.add(Session(token_hash=digest(secrets.token_urlsafe(32)), csrf_hash=digest(secrets.token_urlsafe(32)), user_id=admin.id, created_at=now, last_seen_at=now, expires_at=now+timedelta(hours=1)))
        db.commit()
        synced_messages = seed_users(
            db,
            admin_username=admin_name,
            admin_password="local-admin-secret",
            clinician_username=clinician_name,
            clinician_password="local-clinician-secret",
            sync_demo_passwords=True,
        )
        assert admin.password_hash != admin_hash
        assert clinician.password_hash != clinician_hash
        assert db.query(Session).filter_by(user_id=admin.id).count() == 0
        assert any("synchronized for ADMIN" in item for item in synced_messages)
        assert any("synchronized for SENIOR_CLINICIAN" in item for item in synced_messages)
        assert db.query(AuditLog).filter_by(action="seed.demo_password_sync", object_id=admin.id).count() == 1
        assert db.query(AuditLog).filter_by(action="seed.demo_password_sync", object_id=clinician.id).count() == 1
    finally:
        for username in (admin_name, clinician_name):
            user = db.query(AppUser).filter_by(username=username).one_or_none()
            if user is not None:
                db.query(UserWard).filter_by(user_id=user.id).delete(synchronize_session=False)
                db.delete(user)
        db.commit()
        reset_simulation(db)
        app.state.clock = SystemClock()
        db.close()


def test_local_demo_credentials_fill_form_and_are_not_cached(monkeypatch):
    username = "demo-admin-" + uuid.uuid4().hex[:8]
    password = DEMO_ACCOUNT_PASSWORDS["admin"]
    db = SessionLocal()
    user = AppUser(username=username, password_hash=hasher.hash("old-random-demo-password"), role=Role.ADMIN, active=True)
    previous_enabled, previous_environment = settings.demo_login_enabled, settings.environment
    settings.demo_login_enabled = True
    settings.environment = "development"
    monkeypatch.setenv("SEED_ADMIN_USERNAME", username)
    client = TestClient(app, base_url="http://localhost")
    try:
        db.add(user); db.commit()
        challenge = client.get("/api/v1/auth/csrf")
        csrf = challenge.json()["csrf_token"]
        response = client.post("/api/v1/auth/demo-credentials", headers={"X-CSRF-Token":csrf}, json={"account":"admin"})
        assert response.status_code == 200, response.text
        assert response.json() == {"username":username,"password":password}
        assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
        assert db.query(AuditLog).filter_by(action="auth.demo_credentials_fetch", object_id=user.id).count() == 1
        db.refresh(user)
        assert hasher.verify(user.password_hash, password)
        assert db.query(AuditLog).filter_by(action="auth.demo_credentials_sync", object_id=user.id).count() == 1
    finally:
        db.query(AuditLog).filter_by(object_id=user.id).delete(synchronize_session=False)
        db.delete(user); db.commit(); db.close(); client.close()
        settings.demo_login_enabled, settings.environment = previous_enabled, previous_environment
