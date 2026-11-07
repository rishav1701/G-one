import json
from pathlib import Path

import pandas as pd
import joblib
import yaml

from ml.evaluation import matched_sensitivity_threshold
from ml.features import build_features, feature_names
from ml.fixtures import synthetic_fixture
from ml.labelling import label_outcomes
from ml.predict import predict_probabilities
from ml.splits import grouped_cv_splits, temporal_patient_splits
from ml.pipeline.train import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def test_feature_contract_is_shared_leakage_safe_and_tracks_missingness():
    config = yaml.safe_load((ROOT / "ml/config.yaml").read_text())
    observations, patients, predictions, _ = synthetic_fixture(12)
    frame = build_features(observations, patients, predictions, config)
    assert list(frame.columns) == feature_names(config)
    assert len(frame) == len(predictions)
    assert (frame["latest_respiration_rate"] < 99).all()
    assert (frame["latest_spo2"] > 50).all()
    assert frame["news2_total"].notna().all()
    one_patient = "FIX-0001"
    partial_obs = [row for row in observations if row["patient_id"] == one_patient]
    partial_patient = [row for row in patients if row["patient_id"] == one_patient]
    partial_prediction = [row for row in predictions if row["patient_id"] == one_patient]
    partial_obs = [dict(row, respiration_rate=None, spo2=None, supplemental_o2=None,
                        systolic_bp=None, pulse=None, consciousness=None, temperature=None)
                   for row in partial_obs if row["measured_at"] <= partial_prediction[0]["prediction_at"]]
    incomplete = build_features(partial_obs, partial_patient, partial_prediction, config)
    assert incomplete.iloc[0]["missing_respiration_rate"] == 1
    assert pd.isna(incomplete.iloc[0]["latest_respiration_rate"])


def test_outcome_horizon_censoring_and_post_event_exclusion():
    anchor = pd.Timestamp("2025-01-01T00:00:00Z")
    predictions = [{"patient_id": key, "prediction_at": anchor} for key in ("prior", "within", "later", "censored", "negative")]
    outcomes = [
        {"patient_id": "prior", "event_at": anchor-pd.Timedelta(hours=1), "discharge_at": None, "death_at": None},
        {"patient_id": "within", "event_at": anchor+pd.Timedelta(hours=3), "discharge_at": None, "death_at": None},
        {"patient_id": "later", "event_at": anchor+pd.Timedelta(hours=8), "discharge_at": anchor+pd.Timedelta(days=2), "death_at": None},
        {"patient_id": "censored", "event_at": None, "discharge_at": anchor+pd.Timedelta(hours=2), "death_at": None},
        {"patient_id": "negative", "event_at": None, "discharge_at": anchor+pd.Timedelta(days=1), "death_at": None},
    ]
    labeled = label_outcomes(predictions, outcomes, horizon_hours=6).set_index("patient_id")["label"].to_dict()
    assert pd.isna(labeled["prior"]) and pd.isna(labeled["censored"])
    assert labeled["within"] == 1 and labeled["later"] == 0 and labeled["negative"] == 0


def test_patient_level_temporal_splits_and_grouped_cv_have_no_overlap():
    observations, patients, predictions, outcomes = synthetic_fixture(60)
    config = yaml.safe_load((ROOT / "ml/config.yaml").read_text())
    split = temporal_patient_splits(pd.DataFrame(predictions), config)
    sets = {key: set(value) for key, value in split.items()}
    assert all(not sets[a] & sets[b] for a, b in (("train", "validation"), ("train", "calibration"), ("train", "test"), ("validation", "calibration"), ("validation", "test"), ("calibration", "test")))
    assert max(pd.Timestamp(next(p["prediction_at"] for p in predictions if p["patient_id"] == pid)) for pid in split["train"]) < min(pd.Timestamp(next(p["prediction_at"] for p in predictions if p["patient_id"] == pid)) for pid in split["validation"])
    cv = grouped_cv_splits(split["train"], config)
    for train_index, validation_index in cv:
        assert not set(train_index) & set(validation_index)


def test_matched_sensitivity_threshold_is_bounded_by_reference():
    threshold, reference, achieved = matched_sensitivity_threshold([0, 1, 1, 0], [0.1, 0.8, 0.6, 0.4], [False, True, False, False])
    assert reference == 0.5
    assert achieved >= reference
    assert 0 <= threshold <= 1


def test_zero_reference_sensitivity_with_probability_one_has_no_usable_threshold():
    threshold, reference, achieved = matched_sensitivity_threshold(
        [0, 1], [0.2, 1.0], [False, False]
    )
    assert threshold is None
    assert reference == 0.0
    assert achieved == 0.0


def test_fixture_pipeline_writes_hashed_candidate_and_aggregate_metrics():
    output = ROOT.parent / ".tools" / "ml-test-candidate"
    manifest = run_pipeline(output_dir=output, fixture=True)
    saved_manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["acceptance_passed"] is False
    assert saved_manifest["training_population"] == "Generated synthetic software fixtures only"
    assert not list((ROOT.parent / "models/active").glob("*"))
    for filename, expected_hash in saved_manifest["files"].items():
        import hashlib
        assert hashlib.sha256((output / filename).read_bytes()).hexdigest() == expected_hash
    metrics_text = (output / "metrics.json").read_text()
    metrics = json.loads(metrics_text)
    assert metrics["fixture_only"] is True
    assert metrics["acceptance_criteria"].startswith("Not set by the user")
    assert "FIX-" not in metrics_text
    assert (output / "model.joblib").exists()
    assert (output / "data_fingerprint.json").exists()
    assert metrics["grouped_cross_validation"]["fold_auprc"]
    assert sum(point["n"] for point in metrics["candidate_model"]["calibration_plot_data"]) == metrics["split_counts"]["test"]
    observations, patients, predictions, _ = synthetic_fixture()
    bundle = joblib.load(output / "model.joblib")
    probabilities = predict_probabilities(bundle, observations, patients, predictions, yaml.safe_load((output / "config.yaml").read_text()))
    assert len(probabilities) == len(predictions) and all(0 <= value <= 1 for value in probabilities)
