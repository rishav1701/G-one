import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.auth import digest
from app.core.db import SessionLocal
from app.domain.news2 import calculate_news2
from app.main import app
from app.models.base import (
    Admission, Alert, AlertEvent, ApiKey, AppUser, AuditLog, ClinicalResponse,
    Escalation, IngestionRejection, Observation, Patient, RiskAssessment,
    Role, Session, UserWard, Ward,
)
from app.services.clinical import recompute_stored_assessment


@pytest.fixture
def clinical_data():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    key = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    ward_a = Ward(name=f"Phase 2 A {suffix}")
    ward_b = Ward(name=f"Phase 2 B {suffix}")
    clinician = AppUser(username=f"phase2-clinician-{suffix}", password_hash="unused", role=Role.CLINICIAN, active=True)
    viewer = AppUser(username=f"phase2-viewer-{suffix}", password_hash="unused", role=Role.VIEWER, active=True)
    db.add_all([ward_a, ward_b, clinician, viewer])
    db.flush()
    db.add_all([UserWard(user_id=clinician.id, ward_id=ward_a.id), UserWard(user_id=viewer.id, ward_id=ward_a.id)])
    number = int(suffix, 16) % 1_000_000
    patient_a = Patient(patient_identifier=f"SIM-{number:06d}", age_years=52, sex="F")
    patient_b = Patient(patient_identifier=f"SIM-{(number + 1) % 1_000_000:06d}", age_years=64, sex="M")
    db.add_all([patient_a, patient_b])
    db.flush()
    admission_a = Admission(patient_id=patient_a.id, ward_id=ward_a.id, bed_label="A-01", admitted_at=now-timedelta(days=1), spo2_scale=1, status="ACTIVE")
    admission_b = Admission(patient_id=patient_b.id, ward_id=ward_b.id, bed_label="B-01", admitted_at=now-timedelta(days=1), spo2_scale=2, status="ACTIVE")
    db.add_all([admission_a, admission_b])
    db.add(ApiKey(key_hash=hashlib.sha256(key.encode()).hexdigest(), scope="ingest:write"))
    db.flush()
    session_rows = []
    for user in (clinician, viewer):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        session_rows.append(Session(token_hash=digest(token), csrf_hash=digest(csrf), user_id=user.id, created_at=now, last_seen_at=now, expires_at=now+timedelta(hours=2)))
        user.session_token = token
        user.session_csrf = csrf
    db.add_all(session_rows)
    db.commit()
    bundle = {
        "suffix": suffix, "key": key, "ward_a": ward_a.id, "ward_b": ward_b.id,
        "clinician": clinician, "viewer": viewer, "patient_a": patient_a.id, "patient_b": patient_b.id,
        "admission_a": admission_a.id, "admission_b": admission_b.id,
    }
    db.close()
    yield bundle
    db = SessionLocal()
    user_ids = [bundle["clinician"].id, bundle["viewer"].id]
    admission_ids = [bundle["admission_a"], bundle["admission_b"]]
    patient_ids = [bundle["patient_a"], bundle["patient_b"]]
    observation_ids = [row[0] for row in db.query(Observation.id).filter(Observation.admission_id.in_(admission_ids)).all()]
    assessment_ids = [row[0] for row in db.query(RiskAssessment.id).filter(RiskAssessment.admission_id.in_(admission_ids)).all()]
    rejection_ids = [row[0] for row in db.query(IngestionRejection.id).filter(IngestionRejection.source == f"test-{bundle['suffix']}").all()]
    db.query(Session).filter(Session.user_id.in_(user_ids)).delete(synchronize_session=False)
    alert_ids = [row[0] for row in db.query(Alert.id).filter(Alert.admission_id.in_(admission_ids)).all()]
    db.query(AlertEvent).filter(AlertEvent.alert_id.in_(alert_ids)).delete(synchronize_session=False)
    db.query(ClinicalResponse).filter(ClinicalResponse.alert_id.in_(alert_ids)).delete(synchronize_session=False)
    db.query(Escalation).filter(Escalation.alert_id.in_(alert_ids)).delete(synchronize_session=False)
    db.query(Alert).filter(Alert.id.in_(alert_ids)).delete(synchronize_session=False)
    db.query(RiskAssessment).filter(RiskAssessment.admission_id.in_(admission_ids)).delete(synchronize_session=False)
    db.query(Observation).filter(Observation.admission_id.in_(admission_ids)).delete(synchronize_session=False)
    db.query(IngestionRejection).filter(IngestionRejection.source == f"test-{bundle['suffix']}").delete(synchronize_session=False)
    db.query(Admission).filter(Admission.id.in_(admission_ids)).delete(synchronize_session=False)
    db.query(Patient).filter(Patient.id.in_(patient_ids)).delete(synchronize_session=False)
    db.query(UserWard).filter(UserWard.user_id.in_(user_ids)).delete(synchronize_session=False)
    db.query(ApiKey).filter_by(key_hash=hashlib.sha256(bundle["key"].encode()).hexdigest()).delete(synchronize_session=False)
    db.query(AppUser).filter(AppUser.id.in_(user_ids)).delete(synchronize_session=False)
    db.query(Ward).filter(Ward.id.in_([bundle["ward_a"], bundle["ward_b"]])).delete(synchronize_session=False)
    db.commit()
    db.close()


def user_client(user):
    client = TestClient(app)
    client.cookies.set("g_one_session", user.session_token)
    client.cookies.set("g_one_csrf", user.session_csrf)
    return client


def observation_payload(admission_id, source_id, **overrides):
    payload = {
        "admission_id": admission_id,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "respiration_rate": 12, "spo2": 97, "supplemental_o2": False,
        "systolic_bp": 120, "pulse": 70, "consciousness": "ALERT",
        "temperature": "37.0", "source": "test-" + source_id.split("-")[-1],
        "source_record_id": source_id, "is_simulated": True,
    }
    payload.update(overrides)
    return payload


def test_ingestion_validation_idempotency_and_recomputation(clinical_data):
    client = TestClient(app)
    headers = {"X-API-Key": clinical_data["key"]}
    payload = observation_payload(clinical_data["admission_a"], "record-1-" + clinical_data["suffix"])
    accepted = client.post("/api/v1/observations", json=payload, headers=headers)
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["status"] == "VALID"
    clinician = user_client(clinical_data["clinician"])
    observations = clinician.get(f"/api/v1/admissions/{clinical_data['admission_a']}/observations")
    assert observations.status_code == 200, observations.text
    assert observations.json()[0]["pulse"] == 70
    assessments = clinician.get(f"/api/v1/admissions/{clinical_data['admission_a']}/assessments")
    assert assessments.status_code == 200 and assessments.json()[0]["total"] == 0
    assert assessments.json()[0]["level"] == "LOW"
    monitoring = clinician.get(f"/api/v1/admissions/{clinical_data['admission_a']}/monitoring")
    assert monitoring.status_code == 200, monitoring.text
    assert monitoring.json()["items"][0]["values"]["pulse"] == 70
    assert monitoring.json()["items"][0]["parameter_scores"]["pulse"] == 0
    assert client.post("/api/v1/observations", json=payload, headers=headers).json()["idempotent_replay"] is True
    conflict = dict(payload, pulse=111)
    assert client.post("/api/v1/observations", json=conflict, headers=headers).status_code == 409

    impossible = dict(payload, source_record_id="range-" + clinical_data["suffix"], pulse=301)
    assert client.post("/api/v1/observations", json=impossible, headers=headers).status_code == 422
    future = dict(payload, source_record_id="future-" + clinical_data["suffix"], measured_at=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat())
    assert client.post("/api/v1/observations", json=future, headers=headers).status_code == 422
    malformed_precision = dict(payload, source_record_id="precision-" + clinical_data["suffix"], temperature="37.25")
    assert client.post("/api/v1/observations", json=malformed_precision, headers=headers).status_code == 422

    partial = dict(payload, source_record_id="partial-" + clinical_data["suffix"], respiration_rate=8, spo2=None, supplemental_o2=None, systolic_bp=None, pulse=None, consciousness=None, temperature=None)
    partial_result = client.post("/api/v1/observations", json=partial, headers=headers)
    assert partial_result.status_code == 201, partial_result.text
    db = SessionLocal()
    assessment = db.query(RiskAssessment).filter_by(admission_id=clinical_data["admission_a"]).order_by(RiskAssessment.computed_at.desc()).first()
    recomputed = recompute_stored_assessment(db, assessment.id)
    assert recomputed.explanation() == assessment.explanation
    assert recomputed.total == assessment.total
    rejection_count = db.query(IngestionRejection).filter_by(source="test-" + clinical_data["suffix"]).count()
    assert rejection_count == 4
    db.close()


def test_idor_role_matrix_pagination_and_audit(clinical_data):
    clinician = user_client(clinical_data["clinician"])
    viewer = user_client(clinical_data["viewer"])
    assert clinician.get("/api/v1/admissions?limit=1&offset=0").status_code == 200
    page = clinician.get("/api/v1/admissions?limit=1&offset=0").json()
    assert page["limit"] == 1 and page["total"] == 1
    patient_page = clinician.get("/api/v1/patients?limit=10&offset=0").json()
    assert patient_page["limit"] == 10 and patient_page["total"] == 1 and len(patient_page["items"]) == 1
    assert clinician.get(f"/api/v1/patients/{clinical_data['patient_a']}").status_code == 200
    assert clinician.get(f"/api/v1/admissions/{clinical_data['admission_b']}").status_code == 404
    assert clinician.get(f"/api/v1/patients/{clinical_data['patient_b']}").status_code == 404
    assert viewer.post("/api/v1/observations", json=observation_payload(clinical_data["admission_a"], "viewer-" + clinical_data["suffix"]), headers={"X-CSRF-Token": clinical_data["viewer"].session_csrf}).status_code == 403
    db = SessionLocal()
    assert db.query(AuditLog).filter_by(actor_id=clinical_data["clinician"].id, action="patient.read").count() == 2
    db.close()


def test_ingestion_out_of_order_and_ward_idor(clinical_data):
    clinician = user_client(clinical_data["clinician"])
    too_old = observation_payload(clinical_data["admission_a"], "old-" + clinical_data["suffix"], measured_at=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat())
    assert clinician.post("/api/v1/observations", json=too_old, headers={"X-CSRF-Token": clinical_data["clinician"].session_csrf}).status_code == 201
    scoped_out = observation_payload(clinical_data["admission_b"], "scope-" + clinical_data["suffix"])
    assert clinician.post("/api/v1/observations", json=scoped_out, headers={"X-CSRF-Token": clinical_data["clinician"].session_csrf}).status_code == 404
