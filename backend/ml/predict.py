from collections.abc import Mapping

from ml.features import build_features


def predict_probabilities(model_artifact, observations, patients, predictions, config):
    """Use the shared feature contract on a bundle already loaded by a trusted caller."""
    if not isinstance(model_artifact, Mapping):
        raise TypeError("Pass an already verified model bundle")
    bundle = model_artifact
    features = build_features(observations, patients, predictions, config)
    matrix = features.reindex(columns=bundle["feature_names"]).to_numpy(dtype=float)
    raw = bundle["estimator"].predict_proba(matrix)[:, 1]
    calibrated = bundle["calibrator"].predict(raw)
    return calibrated
