import numpy as np
from datetime import timedelta
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def _summary(y, probability, threshold=0.5):
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    prediction = probability >= threshold
    tp = int(np.sum((prediction == 1) & (y == 1)))
    fp = int(np.sum((prediction == 1) & (y == 0)))
    tn = int(np.sum((prediction == 0) & (y == 0)))
    fn = int(np.sum((prediction == 0) & (y == 1)))
    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    ppv = tp / (tp + fp) if tp + fp else 0.0
    return {
        "auroc": float(roc_auc_score(y, probability)) if len(set(y)) == 2 else None,
        "auprc": float(average_precision_score(y, probability)) if int(y.sum()) else None,
        "prevalence": float(np.mean(y)), "sensitivity": sensitivity,
        "specificity": specificity, "positive_predictive_value": ppv,
        "brier_score": float(brier_score_loss(y, probability)),
        "threshold": float(threshold), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }


def _bootstrap_ci(y, probability, threshold, patients, seed, replicates):
    rng = np.random.default_rng(seed)
    groups = np.asarray(patients)
    unique = np.unique(groups)
    values = {name: [] for name in ("auroc", "auprc", "sensitivity", "specificity", "positive_predictive_value", "brier_score")}
    y, probability = np.asarray(y), np.asarray(probability)
    for _ in range(replicates):
        sampled_groups = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == group) for group in sampled_groups])
        result = _summary(y[indices], probability[indices], threshold)
        for name in values:
            if result[name] is not None:
                values[name].append(result[name])
    return {name: [float(np.percentile(items, 2.5)), float(np.percentile(items, 97.5))] if items else None for name, items in values.items()}


def matched_sensitivity_threshold(y, probability, reference_alert):
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    reference_alert = np.asarray(reference_alert, dtype=bool)
    positives = int(y.sum())
    reference_sensitivity = float(np.sum(reference_alert & (y == 1)) / positives) if positives else 0.0
    candidates = sorted(set(probability.tolist()) | {float(np.nextafter(1.0, 2.0))}, reverse=True)
    scored = []
    for threshold in candidates:
        sensitivity = float(np.sum((probability >= threshold) & (y == 1)) / positives) if positives else 0.0
        scored.append((abs(sensitivity-reference_sensitivity), -threshold, threshold, sensitivity))
    _, _, threshold, sensitivity = min(scored) if scored else (0.0, 0.0, 1.0, 0.0)
    # A threshold above 1 is only a sentinel for the no-alert case. It is not
    # a usable probability threshold, so expose it as unavailable in metrics.
    return (None if threshold > 1.0 else float(threshold)), reference_sensitivity, sensitivity


def evaluate_test_set(y, probability, features, rows, outcomes_by_patient, config, evaluation_threshold=0.5):
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    reference_alert = features["news2_total"].to_numpy(dtype=float) >= int(config["news2_reference_alert_total"])
    threshold, reference_sensitivity, matched_sensitivity = matched_sensitivity_threshold(y, probability, reference_alert)
    summary = _summary(y, probability, threshold=evaluation_threshold)
    summary["patient_bootstrap_95_percent_ci"] = _bootstrap_ci(
        y, probability, evaluation_threshold, rows["patient_id"].astype(str),
        int(config["bootstrap_seed"]), int(config["bootstrap_replicates"]),
    )
    alerts = int(np.sum(probability >= threshold)) if threshold is not None else 0
    patient_days = 0.0
    detection_lead_hours = []
    for index, row in rows.reset_index(drop=True).iterrows():
        outcome = outcomes_by_patient[str(row["patient_id"])]
        anchor = row["prediction_at"]
        censor = outcome.get("discharge_at") or outcome.get("death_at")
        event = outcome.get("event_at")
        end = event if event is not None and event <= (censor or event) else censor
        end = min(end, anchor + timedelta(hours=float(config["prediction_horizon_hours"]))) if end else anchor + timedelta(hours=float(config["prediction_horizon_hours"]))
        patient_days += max(0.0, (end-anchor).total_seconds()/86400)
        if probability[index] >= summary["threshold"] and int(y[index]) == 1 and event is not None:
            detection_lead_hours.append(max(0.0, (event-anchor).total_seconds()/3600))
    summary["news2_reference_threshold"] = int(config["news2_reference_alert_total"])
    summary["news2_reference_sensitivity"] = reference_sensitivity
    summary["matched_sensitivity_threshold"] = threshold
    summary["matched_sensitivity"] = matched_sensitivity
    summary["alerts_per_patient_day_at_matched_sensitivity"] = alerts/patient_days if patient_days else None
    summary["patient_days"] = patient_days
    summary["detection_lead_time_hours"] = {
        "count": len(detection_lead_hours),
        "median": float(np.median(detection_lead_hours)) if detection_lead_hours else None,
        "p10": float(np.percentile(detection_lead_hours, 10)) if detection_lead_hours else None,
        "p90": float(np.percentile(detection_lead_hours, 90)) if detection_lead_hours else None,
    }
    metadata = rows.set_index("patient_id").join(features[["age_years", "sex_F", "sex_M", "sex_OTHER"]])
    sex = np.where(metadata["sex_F"].to_numpy() == 1, "F", np.where(metadata["sex_M"].to_numpy() == 1, "M", "OTHER"))
    metadata["sex_group"] = sex
    labels_by_patient = dict(zip(rows["patient_id"].astype(str), y))
    probability_by_patient = dict(zip(rows["patient_id"].astype(str), probability))
    groups = {}
    for label, group in metadata.groupby("sex_group"):
        yi = np.array([labels_by_patient[str(pid)] for pid in group.index])
        pi = np.array([probability_by_patient[str(pid)] for pid in group.index])
        groups[f"sex_{label}"] = {"n": len(group), **_summary(yi, pi)}
    for name, mask in (("under_50", metadata["age_years"] < 50),
                       ("50_to_69", metadata["age_years"].between(50, 69)),
                       ("70_plus", metadata["age_years"] >= 70)):
        group = metadata.loc[mask]
        yi = np.array([labels_by_patient[str(pid)] for pid in group.index])
        pi = np.array([probability_by_patient[str(pid)] for pid in group.index])
        groups[f"age_{name}"] = {"n": len(group), **_summary(yi, pi)} if len(group) else {"n": 0}
    summary["subgroups"] = groups
    clipped = np.clip(probability, 1e-6, 1-1e-6)
    logits = np.log(clipped / (1-clipped))
    if len(np.unique(logits)) > 1:
        slope, intercept = np.polyfit(logits, y, 1)
        summary["calibration_slope"] = float(slope)
        summary["calibration_intercept"] = float(intercept)
    else:
        summary["calibration_slope"] = None
        summary["calibration_intercept"] = None
    bins = np.linspace(0, 1, 6)
    summary["calibration_plot_data"] = []
    for index, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
        mask = (probability >= low) & ((probability <= high) if index == len(bins)-2 else (probability < high))
        if np.any(mask):
            summary["calibration_plot_data"].append({
                "mean_predicted": float(np.mean(probability[mask])),
                "observed_fraction": float(np.mean(y[mask])), "n": int(np.sum(mask)),
            })
    return summary
