import hashlib
import json
import math
from pathlib import Path

import joblib
import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Admission, ModelPrediction, Observation, Patient, RiskAssessment

ROOT = Path(__file__).resolve().parents[3]
ACTIVE_DIR = ROOT / "models" / "active"
REQUIRED_MANIFEST = {
    "model_id", "version", "created_at", "algorithm", "feature_contract_version",
    "training_population", "outcome", "horizon_hours", "data_source", "acceptance_passed",
    "metrics_ref", "intended_use", "not_validated_for", "files",
}


class InvalidModelArtifact(ValueError):
    pass


def _safe_file(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or "/" in name or "\\" in name or Path(name).name != name or name in ("", ".", ".."):
        raise InvalidModelArtifact("Artifact file reference is invalid")
    path = directory / name
    if path.is_symlink() or path.resolve().parent != directory.resolve() or not path.is_file():
        raise InvalidModelArtifact("Artifact file is unavailable")
    return path


def load_verified_active(directory: Path = ACTIVE_DIR):
    """Return None if no model is deployed; reject incomplete, unaccepted or tampered artifacts."""
    directory = Path(directory)
    if directory.is_symlink():
        raise InvalidModelArtifact("Active artifact directory cannot be a symbolic link")
    directory = directory.resolve()
    if not directory.exists() or not any(directory.iterdir()):
        return None
    manifest_path = _safe_file(directory, "manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidModelArtifact("Artifact manifest cannot be read") from exc
    if not isinstance(manifest, dict) or not REQUIRED_MANIFEST.issubset(manifest):
        raise InvalidModelArtifact("Artifact manifest is incomplete")
    if manifest.get("acceptance_passed") is not True:
        raise InvalidModelArtifact("Artifact has not passed its acceptance criteria")
    files = manifest.get("files")
    if not isinstance(files, dict) or not {"model.joblib", "config.yaml"}.issubset(files):
        raise InvalidModelArtifact("Artifact file manifest is incomplete")
    for name, expected_hash in files.items():
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise InvalidModelArtifact("Artifact file hash is invalid")
        path = _safe_file(directory, name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise InvalidModelArtifact("Artifact file hash does not match its manifest")
    metrics_ref = manifest["metrics_ref"]
    if metrics_ref not in files or metrics_ref in ("", ".", ".."):
        raise InvalidModelArtifact("Verified model metrics are not included in the artifact")
    try:
        metrics = json.loads(_safe_file(directory, metrics_ref).read_text(encoding="utf-8"))
        config = yaml.safe_load(_safe_file(directory, "config.yaml").read_text(encoding="utf-8"))
        bundle = joblib.load(_safe_file(directory, "model.joblib"))
    except Exception as exc:
        raise InvalidModelArtifact("Verified model files could not be loaded") from exc
    if not isinstance(bundle, dict) or bundle.get("contract_version") != manifest["feature_contract_version"]:
        raise InvalidModelArtifact("Model feature contract does not match the manifest")
    if not isinstance(config, dict) or not isinstance(metrics, dict) or metrics.get("fixture_only") is True:
        raise InvalidModelArtifact("Fixture-only metrics cannot be deployed")
    return {"manifest": manifest, "metrics": metrics, "config": config, "bundle": bundle}


def verified_evaluation(directory: Path = ACTIVE_DIR):
    active = load_verified_active(directory)
    if active is None:
        return None
    manifest, metrics = active["manifest"], active["metrics"]
    if metrics.get("fixture_only") is True:
        return None
    return {
        "model_id": manifest["model_id"], "version": manifest["version"],
        "training_population": manifest["training_population"], "horizon_hours": manifest["horizon_hours"],
        "provenance": "Retrospective evaluation on development data, not prospective validation",
        "metrics": metrics,
    }


def persist_prediction(db: Session, admission: Admission, assessment: RiskAssessment, directory: Path = ACTIVE_DIR):
    active = load_verified_active(directory)
    if active is None:
        return None
    manifest = active["manifest"]
    existing = db.scalar(select(ModelPrediction).where(
        ModelPrediction.assessment_id == assessment.id,
        ModelPrediction.model_id == manifest["model_id"],
        ModelPrediction.model_version == manifest["version"],
    ))
    if existing:
        return existing
    patient = db.get(Patient, admission.patient_id)
    observations = db.scalars(select(Observation).where(
        Observation.admission_id == admission.id, Observation.status == "VALID",
        Observation.measured_at <= assessment.computed_at,
    ).order_by(Observation.measured_at)).all()
    from ml.features import build_features
    frame = build_features(
        [{"patient_id": patient.id, "measured_at": row.measured_at, **{
            name: (getattr(row, name).isoformat() if hasattr(getattr(row, name), "isoformat") else getattr(row, name))
            for name in ("respiration_rate", "spo2", "systolic_bp", "pulse", "temperature", "supplemental_o2", "consciousness")
        }} for row in observations],
        [{"patient_id": patient.id, "age_years": patient.age_years, "sex": patient.sex}],
        [{"patient_id": patient.id, "prediction_at": assessment.computed_at, "spo2_scale": admission.spo2_scale}],
        active["config"],
    )
    matrix = frame.reindex(columns=active["bundle"]["feature_names"]).to_numpy(dtype=float)
    raw = float(active["bundle"]["estimator"].predict_proba(matrix)[0, 1])
    probability = float(active["bundle"]["calibrator"].predict([raw])[0])
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise InvalidModelArtifact("Model returned an invalid probability")
    row_values = {key: (None if not math.isfinite(float(value)) else float(value)) for key, value in frame.iloc[0].to_dict().items()}
    feature_hash = hashlib.sha256(json.dumps(row_values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    coefficients = getattr(active["bundle"]["estimator"], "coef_", None)
    names = active["bundle"]["feature_names"]
    top_features = []
    if coefficients is not None:
        top_features = [{"feature": names[index], "coefficient": float(coefficients[0][index])}
                        for index in sorted(range(len(names)), key=lambda item: -abs(coefficients[0][item]))[:5]]
    prediction = ModelPrediction(
        assessment_id=assessment.id, model_id=manifest["model_id"], model_version=manifest["version"],
        probability=probability, calibrated=True, feature_hash=feature_hash,
        explanation={"top_features": top_features, "notice": "Attribution is not causation."},
        interface_demo=admission.is_simulated,
    )
    db.add(prediction)
    db.flush()
    return prediction
