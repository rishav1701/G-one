import argparse
import hashlib
from importlib.metadata import version
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.evaluation import evaluate_test_set
from ml.features import build_features
from ml.fixtures import synthetic_fixture
from ml.labelling import label_outcomes
from ml.splits import grouped_cv_splits, temporal_patient_splits


BACKEND = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = BACKEND / "ml" / "config.yaml"
DEFAULT_OUTPUT = BACKEND.parent / "models" / "candidate"
CHECKPOINT_ROOT = BACKEND.parent / ".tools" / "ml-checkpoints"


def load_config(path=DEFAULT_CONFIG):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _model(name, params, seed):
    if name.startswith("logistic"):
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(C=params["C"], max_iter=1500, random_state=seed)),
        ])
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("classifier", HistGradientBoostingClassifier(
            max_iter=params["max_iter"], max_leaf_nodes=7, learning_rate=0.08,
            l2_regularization=1.0, random_state=seed,
        )),
    ])


def _json_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidates():
    return [
        ("logistic_c_0_1", {"C": 0.1}),
        ("logistic_c_1", {"C": 1.0}),
        ("hist_gb_20", {"max_iter": 20}),
        ("hist_gb_50", {"max_iter": 50}),
    ]


def run_pipeline(*, config_path=DEFAULT_CONFIG, output_dir=DEFAULT_OUTPUT, fixture=True):
    if not fixture:
        raise ValueError("Credentialed data is not accepted by this fixture-only harness")
    config_path, output_dir = Path(config_path), Path(output_dir)
    config = load_config(config_path)
    observations, patients, prediction_points, outcomes = synthetic_fixture()
    features = build_features(observations, patients, prediction_points, config)
    labels = label_outcomes(prediction_points, outcomes, config["prediction_horizon_hours"])
    eligible = labels[labels["label"].notna()].copy()
    eligible["label"] = eligible["label"].astype(int)
    eligible = eligible.sort_values("prediction_at").reset_index(drop=True)
    patient_ids = eligible["patient_id"].astype(str).tolist()
    X = features.loc[patient_ids]
    y = eligible["label"].to_numpy(dtype=int)
    split = temporal_patient_splits(eligible, config)
    positions = {pid: index for index, pid in enumerate(patient_ids)}
    indices = {name: np.array([positions[pid] for pid in ids], dtype=int) for name, ids in split.items()}
    if min(np.sum(y[indices[name]] == 1) for name in ("train", "validation", "calibration", "test")) == 0:
        raise ValueError("Each split must include at least one fixture event")

    feature_matrix = X.to_numpy(dtype=float)
    train_x, train_y = feature_matrix[indices["train"]], y[indices["train"]]
    validation_x, validation_y = feature_matrix[indices["validation"]], y[indices["validation"]]
    signature_data = {
        "contract": config["feature_contract_version"], "config": config,
        "patients": len(patients), "observations": len(observations), "eligible": len(eligible),
        "prevalence": float(np.mean(y)),
    }
    signature = hashlib.sha256(json.dumps(signature_data, sort_keys=True).encode()).hexdigest()
    checkpoint_dir = CHECKPOINT_ROOT / signature
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8")) if checkpoint_path.exists() else {"signature": signature, "completed": {}}
    if checkpoint.get("signature") != signature:
        checkpoint = {"signature": signature, "completed": {}}
    deadline = time.monotonic() + float(config["max_train_hours"]) * 3600
    validation_results = {}
    fitted_candidates = {}
    for name, params in _candidates():
        candidate_path = checkpoint_dir / f"{name}.joblib"
        if name in checkpoint["completed"] and candidate_path.exists():
            estimator = joblib.load(candidate_path)
            score = float(checkpoint["completed"][name]["validation_auprc"])
        else:
            if time.monotonic() >= deadline:
                break
            estimator = _model(name, params, int(config["random_seed"]))
            estimator.fit(train_x, train_y)
            validation_probability = estimator.predict_proba(validation_x)[:, 1]
            score = float(average_precision_score(validation_y, validation_probability))
            joblib.dump(estimator, candidate_path)
            checkpoint["completed"][name] = {"validation_auprc": score, "candidate_file": candidate_path.name}
            _json_write(checkpoint_path, checkpoint)
        fitted_candidates[name] = (estimator, params, score)
        validation_results[name] = score
    if not fitted_candidates:
        raise TimeoutError("max_train_hours elapsed before a candidate completed; rerun to resume from checkpoints")
    selected_name = sorted(fitted_candidates, key=lambda name: (-fitted_candidates[name][2], name))[0]
    _, selected_params, selected_validation_auprc = fitted_candidates[selected_name]

    cv_splits = grouped_cv_splits(split["train"], config)
    cv_scores = []
    for fold_train, fold_valid in cv_splits:
        estimator = _model("logistic_c_1", {"C": 1.0}, int(config["random_seed"]))
        fold_train_ix = indices["train"][fold_train]
        fold_valid_ix = indices["train"][fold_valid]
        estimator.fit(feature_matrix[fold_train_ix], y[fold_train_ix])
        probabilities = estimator.predict_proba(feature_matrix[fold_valid_ix])[:, 1]
        cv_scores.append(float(average_precision_score(y[fold_valid_ix], probabilities)))

    fit_indices = np.concatenate((indices["train"], indices["validation"]))
    final_estimator = _model(selected_name, selected_params, int(config["random_seed"]))
    final_estimator.fit(feature_matrix[fit_indices], y[fit_indices])
    calibration_probability = final_estimator.predict_proba(feature_matrix[indices["calibration"]])[:, 1]
    calibrator = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
    calibrator.fit(calibration_probability, y[indices["calibration"]])
    test_probability = final_estimator.predict_proba(feature_matrix[indices["test"]])[:, 1]
    calibrated_test_probability = calibrator.predict(test_probability)

    test_rows = eligible.iloc[indices["test"]].reset_index(drop=True)
    test_ids = test_rows["patient_id"].astype(str).tolist()
    test_features = features.loc[test_ids]
    test_labels = y[indices["test"]]
    outcomes_by_patient = {str(item["patient_id"]): item for item in outcomes}
    candidate_metrics = evaluate_test_set(test_labels, calibrated_test_probability, test_features, test_rows, outcomes_by_patient, config)
    reference_probability = np.clip(test_features["news2_total"].to_numpy(dtype=float) / 19.0, 0, 1)
    reference_metrics = evaluate_test_set(
        test_labels, reference_probability, test_features, test_rows, outcomes_by_patient,
        config, evaluation_threshold=float(config["news2_reference_alert_total"]) / 19.0,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "model.joblib"
    joblib.dump({"estimator": final_estimator, "calibrator": calibrator,
                 "feature_names": list(X.columns), "contract_version": config["feature_contract_version"]}, bundle_path)
    calibration_path = output_dir / "calibration.json"
    _json_write(calibration_path, {"method": "isotonic", "x_thresholds": calibrator.X_thresholds_.tolist(),
                                   "y_thresholds": calibrator.y_thresholds_.tolist(), "split": "calibration"})
    feature_path = output_dir / "feature_list.json"
    _json_write(feature_path, {"feature_contract_version": config["feature_contract_version"], "features": list(X.columns)})
    fingerprint = hashlib.sha256(json.dumps({"cohort": "synthetic fixture v1", "patients": len(patients),
                                             "observations": len(observations), "eligible_predictions": len(eligible),
                                             "horizon_hours": config["prediction_horizon_hours"]}, sort_keys=True).encode()).hexdigest()
    _json_write(output_dir / "data_fingerprint.json", {"cohort_definition": "synthetic fixture v1", "patient_count": len(patients),
                                                        "observation_count": len(observations), "prediction_count": len(eligible),
                                                        "positive_count": int(y.sum()), "cohort_definition_sha256": fingerprint})
    _json_write(output_dir / "metrics.json", {
        "provenance": "synthetic fixture only; not model performance evidence",
        "fixture_only": True, "candidate_model": candidate_metrics, "news2_reference": reference_metrics,
        "model_selection": {"selected_candidate": selected_name, "validation_auprc": selected_validation_auprc,
                            "validation_candidate_auprc": validation_results},
        "grouped_cross_validation": {"method": "GroupKFold by patient within training split", "fold_auprc": cv_scores,
                                     "mean_auprc": float(np.mean(cv_scores))},
        "split_counts": {name: len(ids) for name, ids in split.items()},
        "acceptance_criteria": "Not set by the user; no acceptance decision is made.",
    })
    (output_dir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    versions = {
        "python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__,
        "scikit-learn": __import__("sklearn").__version__, "joblib": joblib.__version__,
        "scipy": __import__("scipy").__version__, "PyYAML": yaml.__version__,
    }
    lock_lines = [f"# Python {versions['python']}"] + [
        f"{name}=={version}" for name, version in versions.items() if name != "python"
    ]
    lock_lines.append(f"tzdata=={version('tzdata')}")
    (output_dir / "environment.lock").write_text("\n".join(lock_lines) + "\n", encoding="utf-8")
    (output_dir / "model_card.md").write_text(
        "# Candidate model card (synthetic fixture only)\n\n"
        "This artifact was trained and evaluated only on generated software fixtures to verify the pipeline. "
        "It is not a clinical model, was not trained on patient data, and must never be promoted to models/active. "
        "It has no clinical meaning and no acceptance criteria have been supplied.\n\n"
        "The reference, candidate, and reported metrics are fixture checks only. There is no prospective validation, "
        "local clinical review, population representativeness, or regulatory assessment.\n",
        encoding="utf-8",
    )
    files = sorted(path for path in output_dir.iterdir() if path.is_file() and path.name != "manifest.json")
    manifest = {
        "model_id": "fixture-only-candidate", "version": "0.0.1", "created_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": selected_name, "feature_contract_version": config["feature_contract_version"],
        "training_population": "Generated synthetic software fixtures only",
        "outcome": "Synthetic deterioration event within the configured horizon",
        "horizon_hours": config["prediction_horizon_hours"], "data_source": "synthetic fixture generator",
        "acceptance_passed": False, "metrics_ref": "metrics.json",
        "intended_use": "Offline pipeline verification only; not for clinical use",
        "not_validated_for": ["clinical use", "patient care", "general-ward population", "prospective use"],
        "calibration_method": "isotonic on separate calibration split",
        "split_strategy": "patient-level chronological train/validation/calibration/test",
        "files": {path.name: _sha256(path) for path in files},
    }
    _json_write(output_dir / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Run the fixture-only G One ML pipeline.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--fixture", action="store_true", help="Required; the harness rejects credentialed data")
    args = parser.parse_args()
    if not args.fixture:
        raise SystemExit("Pass --fixture. This harness accepts only generated software fixtures.")
    print(json.dumps(run_pipeline(config_path=args.config, output_dir=args.output, fixture=True), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
