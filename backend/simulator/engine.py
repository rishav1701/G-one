import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models.base import (
    Admission, Alert, AlertEvent, ApiKey, AuditLog, ClinicalResponse, DataSourceStatus,
    Escalation, IngestionRejection, LabResult, Observation, Patient,
    RiskAssessment, SystemConfig, Ward,
)
from app.services.clinical import refresh_current_assessment

SCENARIOS = (
    "stable", "gradual_deterioration", "sudden_concerning_change",
    "missing_observations", "sensor_disconnection", "data_quality_problems",
)
BASELINE = {
    "respiration_rate": 12, "spo2": 97, "supplemental_o2": False,
    "systolic_bp": 120, "pulse": 70, "consciousness": "ALERT", "temperature": "37.0",
}
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class SimulatedClock:
    current: datetime
    refresh_assessments: bool = False

    def now(self):
        return self.current

    def advance(self, **kwargs):
        self.current += timedelta(**kwargs)
        self.refresh_assessments = True
        return self.current


def _id(seed: int, label: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"gone-simulator:{seed}:{label}"))


def _clear_existing(db: Session, seed: int | None = None):
    admission_ids = list(db.scalars(select(Admission.id).where(Admission.simulation_scenario.is_not(None))).all())
    alert_ids = list(db.scalars(select(Alert.id).where(Alert.admission_id.in_(admission_ids))).all()) if admission_ids else []
    if alert_ids:
        db.query(AlertEvent).filter(AlertEvent.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        db.query(ClinicalResponse).filter(ClinicalResponse.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        db.query(Escalation).filter(Escalation.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        db.query(Alert).filter(Alert.id.in_(alert_ids)).delete(synchronize_session=False)
    if admission_ids:
        db.query(RiskAssessment).filter(RiskAssessment.admission_id.in_(admission_ids)).delete(synchronize_session=False)
        db.query(Observation).filter(Observation.admission_id.in_(admission_ids)).delete(synchronize_session=False)
        db.query(IngestionRejection).filter(IngestionRejection.admission_id.in_(admission_ids)).delete(synchronize_session=False)
        db.query(LabResult).filter(LabResult.admission_id.in_(admission_ids)).delete(synchronize_session=False)
        patient_ids = list(db.scalars(select(Admission.patient_id).where(Admission.id.in_(admission_ids))).all())
        ward_ids = list(db.scalars(select(Admission.ward_id).where(Admission.id.in_(admission_ids)).distinct()).all())
        db.query(Admission).filter(Admission.id.in_(admission_ids)).delete(synchronize_session=False)
        if patient_ids:
            db.query(Patient).filter(Patient.id.in_(patient_ids)).delete(synchronize_session=False)
        if ward_ids:
            db.query(Ward).filter(Ward.id.in_(ward_ids), Ward.name.like("Simulation Ward %")).delete(synchronize_session=False)
    db.query(DataSourceStatus).filter(DataSourceStatus.source.like("sim-%")).delete(synchronize_session=False)
    key_pointer = db.get(SystemConfig, "simulator_machine_key_id")
    if key_pointer:
        db.query(ApiKey).filter(ApiKey.id == key_pointer.value).delete(synchronize_session=False)
        db.delete(key_pointer)
    if seed is not None:
        db.query(ApiKey).filter(ApiKey.id == _id(seed, "machine-key")).delete(synchronize_session=False)
    for key, value in {
        "minimum_alert_level": "LOW_MEDIUM", "alert_downgrade_assessments": "2",
        "alert_escalation_delay_minutes": "5", "alert_escalation_check_seconds": "10",
    }.items():
        row = db.get(SystemConfig, key)
        if row:
            row.value = value
    db.commit()


def _seed_rows(db: Session, seed: int, clock: SimulatedClock):
    wards = [Ward(id=_id(seed, f"ward-{i}"), name=f"Simulation Ward {i}") for i in (1, 2)]
    db.add_all(wards)
    db.flush()
    admissions: dict[str, list[Admission]] = {scenario: [] for scenario in SCENARIOS}
    patients_by_scenario: dict[str, list[Patient]] = {scenario: [] for scenario in SCENARIOS}
    for scenario_index, scenario in enumerate(SCENARIOS):
        for replicate in range(2):
            number = scenario_index * 2 + replicate + 1
            patient = Patient(
                id=_id(seed, f"patient-{number}"), patient_identifier=f"SIM-{number:06d}",
                age_years=35 + number, sex="F" if number % 2 else "M", is_simulated=True,
            )
            db.add(patient)
            db.add(AuditLog(actor_id=None, action="simulator.patient_seeded", object_type="patient", object_id=patient.id,
                            request_id=_id(seed, f"request-patient-{number}"), created_at=clock.now()))
            db.flush()
            admission = Admission(
                id=_id(seed, f"admission-{number}"), patient_id=patient.id,
                ward_id=wards[replicate].id, bed_label=f"{replicate + 1}-{number:02d}",
                admitted_at=clock.now(), spo2_scale=1, status="ACTIVE", is_simulated=True,
                simulation_scenario=scenario,
            )
            db.add(admission)
            db.add(AuditLog(actor_id=None, action="simulator.admission_seeded", object_type="admission", object_id=admission.id,
                            request_id=_id(seed, f"request-admission-{number}"), created_at=clock.now()))
            admissions[scenario].append(admission)
            patients_by_scenario[scenario].append(patient)
            if replicate == 0:
                db.add_all([
                    LabResult(id=_id(seed, f"lab-{number}-hb"), admission_id=admission.id,
                              test_code="Haemoglobin", value="136", unit="g/L", measured_at=clock.now(), is_simulated=True),
                    LabResult(id=_id(seed, f"lab-{number}-crp"), admission_id=admission.id,
                              test_code="C-reactive protein", value="8", unit="mg/L", measured_at=clock.now(), is_simulated=True),
                ])
    raw_key = secrets.token_urlsafe(32)
    key_id = _id(seed, "machine-key")
    db.add(ApiKey(id=key_id, key_hash=hashlib.sha256(raw_key.encode()).hexdigest(), scope="ingest:write"))
    db.add(SystemConfig(key="simulator_machine_key_id", value=key_id))
    for scenario in SCENARIOS:
        for ward_index, ward in enumerate(wards, start=1):
            source = f"sim-{scenario}-ward-{ward_index}"
            status = DataSourceStatus(
                id=_id(seed, f"source-{scenario}-{ward_index}"), source=source,
                ward_id=ward.id, connected=True, is_simulated=True,
                updated_at=clock.now(), status_code="CONNECTED",
            )
            db.add(status)
            db.add(AuditLog(actor_id=None, action="simulator.data_source_seeded", object_type="data_source_status",
                            object_id=status.id, request_id=_id(seed, f"request-{scenario}-{ward_index}"), created_at=clock.now()))
    db.commit()
    return raw_key, admissions, patients_by_scenario


def _measurement(scenario: str, step: int):
    if scenario == "gradual_deterioration" and step == 1:
        return BASELINE | {"respiration_rate": 21}
    if scenario == "gradual_deterioration" and step == 2:
        return BASELINE | {"respiration_rate": 25}
    if scenario == "sudden_concerning_change" and step == 1:
        return {
            "respiration_rate": 8, "spo2": 88, "supplemental_o2": True,
            "systolic_bp": 90, "pulse": 131, "consciousness": "NEW_CONFUSION", "temperature": "39.1",
        }
    if scenario == "missing_observations":
        return {"respiration_rate": 12}
    return dict(BASELINE)


def _post(client, key: str, admission: Admission, scenario: str, step: int, measured_at: datetime, values: dict):
    source_id = f"{scenario}-{admission.id[-6:]}-{step}"
    payload = {
        "admission_id": admission.id, "measured_at": measured_at.isoformat(),
        "source": "simulator", "source_record_id": source_id, "is_simulated": True,
    } | values
    return client.post("/api/v1/observations", json=payload, headers={"X-API-Key": key}), payload


def run_seed(db: Session, seed: int) -> dict:
    clock = SimulatedClock(START)
    app.state.clock = clock
    _clear_existing(db, seed)
    key, admissions, patients = _seed_rows(db, seed, clock)
    output: list[dict] = []
    with TestClient(app) as client:
        app.state.clock = clock
        for scenario in SCENARIOS:
            patient_admissions = admissions[scenario]
            steps = {"stable": 3, "gradual_deterioration": 3, "sudden_concerning_change": 2,
                     "missing_observations": 1, "sensor_disconnection": 1, "data_quality_problems": 1}[scenario]
            last_payloads = {}
            for step in range(steps):
                measurement_time = clock.now()
                for admission in patient_admissions:
                    values = _measurement(scenario, step)
                    response, payload = _post(client, key, admission, scenario, step, measurement_time, values)
                    if response.status_code != 201:
                        raise RuntimeError(f"Simulator ingestion failed: {response.status_code}")
                    last_payloads[admission.id] = payload
                    db.expire_all()
                    assessment = db.scalar(select(RiskAssessment).where(RiskAssessment.admission_id == admission.id).order_by(RiskAssessment.computed_at.desc()).limit(1))
                    alert = db.scalar(select(Alert).where(Alert.admission_id == admission.id, Alert.status.in_(("OPEN", "ACKNOWLEDGED"))))
                    output.append({"scenario": scenario, "patient": next(p.patient_identifier for p in patients[scenario] if p.id == admission.patient_id),
                                   "step": step, "observation_status": response.json()["status"],
                                   "level": assessment.level, "total": assessment.total,
                                   "alert_level": alert.level if alert else None})
                if step < steps - 1:
                    clock.advance(minutes=15)

            if scenario == "sensor_disconnection":
                clock.advance(hours=25)
                statuses = db.query(DataSourceStatus).filter(DataSourceStatus.source.like("sim-sensor_disconnection-%")).all()
                for status in statuses:
                    status.connected, status.status_code, status.updated_at = False, "DISCONNECTED", clock.now()
                    db.add(AuditLog(actor_id=None, action="simulator.data_source_disconnected", object_type="data_source_status",
                                    object_id=status.id, request_id=_id(seed, f"request-disconnected-{status.id}"), created_at=clock.now()))
                for admission in patient_admissions:
                    result = refresh_current_assessment(db, admission, clock.now())
                    output.append({"scenario": scenario, "patient": next(p.patient_identifier for p in patients[scenario] if p.id == admission.patient_id),
                                   "step": "disconnected", "level": result.level, "total": result.total, "alert_level": None})

            if scenario == "data_quality_problems":
                for admission in patient_admissions:
                    original = last_payloads[admission.id]
                    replay = client.post("/api/v1/observations", json=original, headers={"X-API-Key": key})
                    conflict = dict(original, pulse=80)
                    conflict_response = client.post("/api/v1/observations", json=conflict, headers={"X-API-Key": key})
                    impossible = dict(original, source_record_id=original["source_record_id"] + "-bad", pulse=301)
                    rejection = client.post("/api/v1/observations", json=impossible, headers={"X-API-Key": key})
                    old_time = clock.now() - timedelta(hours=1)
                    old_payload = dict(original, source_record_id=original["source_record_id"] + "-old", measured_at=old_time.isoformat())
                    out_of_order = client.post("/api/v1/observations", json=old_payload, headers={"X-API-Key": key})
                    if not (replay.json().get("idempotent_replay") is True and conflict_response.status_code == 409 and rejection.status_code == 422 and out_of_order.status_code == 201):
                        raise RuntimeError("Data-quality scenario assertions failed")
                    output.append({"scenario": scenario, "patient": next(p.patient_identifier for p in patients[scenario] if p.id == admission.patient_id),
                                   "step": "data_quality", "duplicate_replay": True, "conflict_rejected": True,
                                   "hard_range_rejected": True, "out_of_order_accepted": True})

        db.commit()
    canonical = json.dumps({"seed": seed, "events": output}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {"seed": seed, "patients": 12, "wards": 2, "scenarios": list(SCENARIOS),
            "events": output, "output_sha256": hashlib.sha256(canonical).hexdigest()}


def reset_simulation(db: Session):
    _clear_existing(db)
