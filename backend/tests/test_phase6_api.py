import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.auth import digest
from app.core.db import SessionLocal
from app.domain.clock import SystemClock
from app.main import app
from app.models.base import Admission, AppUser, ModelPrediction, Observation, Patient, RiskAssessment, Role, Session, UserWard, Ward
from app.services.model_registry import InvalidModelArtifact, load_verified_active, persist_prediction, verified_evaluation
from ml.features import feature_names


class FixtureEstimator:
    def predict_proba(self, values):
        return np.column_stack((np.full(len(values), .75), np.full(len(values), .25)))


class FixtureCalibrator:
    def predict(self, values):
        return np.full(len(values), .2)


def _fixture_artifact(directory, *, accepted=True):
    directory.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((__import__("pathlib").Path(__file__).parents[1] / "ml/config.yaml").read_text())
    (directory / "config.yaml").write_text(yaml.safe_dump(config))
    (directory / "metrics.json").write_text(json.dumps({"software_test_fixture": True, "candidate_model": {"auroc": .5}}))
    joblib.dump({"estimator": FixtureEstimator(), "calibrator": FixtureCalibrator(),
                 "feature_names": feature_names(config), "contract_version": config["feature_contract_version"]}, directory / "model.joblib")
    hashes = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in ("config.yaml", "metrics.json", "model.joblib")}
    manifest = {
        "model_id": "phase6-software-test-fixture", "version": "test-only", "created_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "test-double", "feature_contract_version": config["feature_contract_version"],
        "training_population": "Clearly marked software integration fixture", "outcome": "Test fixture only",
        "horizon_hours": 6, "data_source": "Temporary test fixture", "acceptance_passed": accepted,
        "metrics_ref": "metrics.json", "intended_use": "Automated integration test only",
        "not_validated_for": ["clinical use"], "files": hashes,
    }
    (directory / "manifest.json").write_text(json.dumps(manifest))
    return directory


@pytest.fixture
def admin_client():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    ward = Ward(name=f"Phase 6 test {suffix}")
    admin = AppUser(username=f"phase6-admin-{suffix}", password_hash="unused", role=Role.ADMIN, active=True)
    db.add_all([ward, admin]); db.flush()
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add_all([UserWard(user_id=admin.id, ward_id=ward.id), Session(token_hash=digest(token), csrf_hash=digest(csrf), user_id=admin.id,
        created_at=now, last_seen_at=now, expires_at=now + timedelta(hours=2))])
    db.commit(); db.close()
    client = TestClient(app)
    client.cookies.set("g_one_session", token); client.cookies.set("g_one_csrf", csrf)
    yield client, {"X-CSRF-Token": csrf}, ward.id
    client.close()
    db = SessionLocal()
    db.query(Session).filter_by(user_id=admin.id).delete(synchronize_session=False)
    db.query(UserWard).filter_by(user_id=admin.id).delete(synchronize_session=False)
    db.delete(admin); db.delete(ward); db.commit(); db.close()
    app.state.clock = SystemClock()


def test_analytics_is_computed_from_database_and_labs_are_ward_scoped(admin_client):
    client, headers, assigned_ward = admin_client
    reset = client.post("/api/v1/admin/simulator/reset", headers=headers, json={"seed": 42})
    assert reset.status_code == 200, reset.text
    first = client.get("/api/v1/analytics").json()
    assert first["source"] == "Application database at request time"
    assert len(first["scenario_outcomes"]) == 6
    assert first["model_state"] == "none" and first["model_evaluation"] is None
    assert first["operational"]["assessed_admissions"] == 12
    disabled_model_alerts = client.put("/api/v1/settings/operational", headers=headers, json={"model_alerting_enabled": "true"})
    assert disabled_model_alerts.status_code == 422
    admissions = client.get("/api/v1/admissions?limit=200").json()["items"]
    admission = next(item for item in admissions if item["patient_identifier"] == "SIM-000001")
    labs = client.get(f"/api/v1/admissions/{admission['id']}/labs")
    assert labs.status_code == 200 and len(labs.json()["items"]) == 2
    assert all(row["is_simulated"] for row in labs.json()["items"])
    assert client.get(f"/api/v1/admissions/{admission['id']}/model-predictions").json()["items"] == []
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    viewer = AppUser(username=f"phase6-viewer-{uuid.uuid4().hex[:8]}", password_hash="unused", role=Role.VIEWER, active=True)
    db.add(viewer); db.flush()
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add_all([UserWard(user_id=viewer.id, ward_id=assigned_ward), Session(token_hash=digest(token), csrf_hash=digest(csrf), user_id=viewer.id,
        created_at=now, last_seen_at=now, expires_at=now + timedelta(hours=2))])
    db.commit(); viewer_id=viewer.id; db.close()
    viewer_client=TestClient(app); viewer_client.cookies.set("g_one_session", token)
    assert viewer_client.get(f"/api/v1/admissions/{admission['id']}/labs").status_code == 404
    viewer_client.close()
    db=SessionLocal(); db.query(Session).filter_by(user_id=viewer_id).delete(synchronize_session=False)
    db.query(UserWard).filter_by(user_id=viewer_id).delete(synchronize_session=False); db.query(AppUser).filter_by(id=viewer_id).delete(synchronize_session=False); db.commit(); db.close()

    db = SessionLocal()
    assessment = db.scalar(select(RiskAssessment).where(RiskAssessment.admission_id == admission["id"]).order_by(RiskAssessment.computed_at.desc()))
    original = assessment.completeness
    assessment.completeness = max(0, original - 1)
    db.commit(); db.close()
    changed = client.get("/api/v1/analytics").json()
    assert changed["operational"]["data_completeness_rate"] != first["operational"]["data_completeness_rate"]
    client.post("/api/v1/admin/simulator/reset", headers=headers, json={"seed": 42})


def test_model_registry_rejects_unaccepted_and_tampered_artifacts(tmp_path):
    empty = tmp_path / "empty"
    assert load_verified_active(empty) is None
    unaccepted = _fixture_artifact(tmp_path / "unaccepted", accepted=False)
    with pytest.raises(InvalidModelArtifact, match="acceptance"):
        load_verified_active(unaccepted)
    tampered = _fixture_artifact(tmp_path / "tampered")
    (tampered / "metrics.json").write_text("{}")
    with pytest.raises(InvalidModelArtifact, match="hash"):
        load_verified_active(tampered)


def test_verified_test_fixture_runs_shared_inference_and_persists_demo_prediction(tmp_path):
    artifact = _fixture_artifact(tmp_path / "active-fixture")
    assert load_verified_active(artifact)["manifest"]["training_population"] == "Clearly marked software integration fixture"
    assert verified_evaluation(artifact)["metrics"]["software_test_fixture"] is True
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]
    ward = Ward(name=f"Model test {suffix}")
    patient = Patient(patient_identifier=f"SIM-{int(suffix, 16) % 1000000:06d}", age_years=57, sex="F", is_simulated=True)
    db.add_all([ward, patient]); db.flush()
    admission = Admission(patient_id=patient.id, ward_id=ward.id, bed_label="T-01", admitted_at=datetime.now(timezone.utc),
                         spo2_scale=1, status="ACTIVE", is_simulated=True)
    db.add(admission); db.flush()
    observation = Observation(admission_id=admission.id, measured_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        respiration_rate=12, spo2=97, supplemental_o2=False, systolic_bp=120, pulse=70, consciousness="ALERT", temperature=37.0,
        source="test", source_record_id=suffix, is_simulated=True, status="VALID", payload_hash="0" * 64)
    db.add(observation); db.flush()
    assessment = RiskAssessment(admission_id=admission.id, scoring_version="test", spo2_scale=1, observation_ids=[observation.id],
        per_parameter_scores={}, completeness=7, level="LOW", total=0, explanation={}, computed_at=observation.measured_at)
    db.add(assessment); db.flush()
    prediction = persist_prediction(db, admission, assessment, artifact)
    db.commit()
    saved = db.get(ModelPrediction, prediction.id)
    assert float(saved.probability) == pytest.approx(.2)
    assert saved.interface_demo is True and len(saved.feature_hash) == 64
    db.query(ModelPrediction).filter_by(id=saved.id).delete(synchronize_session=False)
    db.query(RiskAssessment).filter_by(id=assessment.id).delete(synchronize_session=False)
    db.query(Observation).filter_by(id=observation.id).delete(synchronize_session=False)
    db.query(Admission).filter_by(id=admission.id).delete(synchronize_session=False)
    db.query(Patient).filter_by(id=patient.id).delete(synchronize_session=False)
    db.query(Ward).filter_by(id=ward.id).delete(synchronize_session=False)
    db.commit(); db.close()
