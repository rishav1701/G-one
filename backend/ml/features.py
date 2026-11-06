import numpy as np
import pandas as pd

from app.domain.news2 import PARAMETERS, SpO2Scale, calculate_news2

def raw_feature_parameters(config: dict) -> tuple[str, ...]:
    return tuple("consciousness_non_alert" if name == "consciousness" else name for name in config["raw_parameters"])


def _num(value):
    if value is None or pd.isna(value):
        return np.nan
    if isinstance(value, str):
        return 0.0 if value == "ALERT" else 1.0
    if isinstance(value, bool):
        return float(value)
    return float(value)


def feature_names(config: dict) -> list[str]:
    names = ["age_years", "sex_F", "sex_M", "sex_OTHER"]
    for parameter in raw_feature_parameters(config):
        names.extend((f"latest_{parameter}", f"hours_since_{parameter}"))
        for window in config["rolling_windows_hours"]:
            for suffix in ("min", "max", "mean", "slope", "count"):
                names.append(f"{parameter}_{suffix}_{window}h")
        names.append(f"missing_{parameter}")
    names.extend(f"news2_{parameter}" for parameter in PARAMETERS)
    names.extend(("news2_total", "news2_level_rank", "news2_completeness"))
    return names


def build_features(observations, patients, predictions, config: dict) -> pd.DataFrame:
    """Build prediction-time features using rows measured no later than each anchor."""
    obs = pd.DataFrame(observations).copy()
    people = {str(person["patient_id"]): person for person in patients}
    if not obs.empty:
        obs["measured_at"] = pd.to_datetime(obs["measured_at"], utc=True)
    rows = []
    feature_parameters = raw_feature_parameters(config)
    for point in predictions:
        patient_id = str(point["patient_id"])
        anchor = pd.Timestamp(point["prediction_at"])
        if anchor.tzinfo is None:
            raise ValueError("prediction_at must be timezone-aware")
        anchor = anchor.tz_convert("UTC")
        cutoff = anchor - pd.Timedelta(hours=config["observation_window_hours"])
        history = obs[(obs["patient_id"].astype(str) == patient_id) & (obs["measured_at"] <= anchor) & (obs["measured_at"] >= cutoff)].sort_values("measured_at")
        patient = people[patient_id]
        row = {"age_years": float(patient["age_years"]), "sex_F": float(patient["sex"] == "F"),
               "sex_M": float(patient["sex"] == "M"), "sex_OTHER": float(patient["sex"] not in ("F", "M"))}
        latest_values = {name: None for name in PARAMETERS}
        for parameter in feature_parameters:
            source_parameter = "consciousness" if parameter == "consciousness_non_alert" else parameter
            present = history[history[source_parameter].notna()] if not history.empty else history
            if present.empty:
                latest, latest_at = None, None
            else:
                latest_row = present.iloc[-1]
                latest, latest_at = latest_row[source_parameter], latest_row["measured_at"]
            latest_num = _num(latest)
            row[f"latest_{parameter}"] = latest_num
            row[f"hours_since_{parameter}"] = (anchor - latest_at).total_seconds() / 3600 if latest_at is not None else np.nan
            for window in config["rolling_windows_hours"]:
                window_start = anchor - pd.Timedelta(hours=window)
                if present.empty:
                    window_values = np.array([], dtype=float)
                    x_hours = np.array([], dtype=float)
                else:
                    within = present[present["measured_at"] >= window_start]
                    window_values = np.array([_num(value) for value in within[source_parameter]], dtype=float)
                    x_hours = np.array([(stamp - anchor).total_seconds() / 3600 for stamp in within["measured_at"]], dtype=float)
                aggregates = (
                    ("min", np.min(window_values) if len(window_values) else np.nan),
                    ("max", np.max(window_values) if len(window_values) else np.nan),
                    ("mean", np.mean(window_values) if len(window_values) else np.nan),
                    ("slope", float(np.polyfit(x_hours, window_values, 1)[0]) if len(window_values) >= 2 and np.ptp(x_hours) > 0 else np.nan),
                    ("count", float(len(window_values))),
                )
                for suffix, value in aggregates:
                    row[f"{parameter}_{suffix}_{window}h"] = value
            row[f"missing_{parameter}"] = float(latest is None)
            if source_parameter in latest_values:
                latest_values[source_parameter] = latest
        assessment = calculate_news2(latest_values, spo2_scale=SpO2Scale(int(point.get("spo2_scale", 1))), no_data=not history.shape[0])
        for parameter in PARAMETERS:
            row[f"news2_{parameter}"] = float(assessment.scores.get(parameter, np.nan))
        row["news2_total"] = float(assessment.total)
        row["news2_level_rank"] = float({"NO_DATA": 0, "INCOMPLETE": 1, "LOW": 2, "LOW_MEDIUM": 3, "MEDIUM": 4, "HIGH": 5}[assessment.level.value])
        row["news2_completeness"] = float(assessment.completeness)
        rows.append(row)
    return pd.DataFrame(rows, columns=feature_names(config), index=[str(item["patient_id"]) for item in predictions])
