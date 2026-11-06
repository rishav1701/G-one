import pandas as pd


def label_outcomes(predictions, outcomes, horizon_hours: float) -> pd.DataFrame:
    """Label prediction rows while excluding post-event features and censored horizons."""
    table = pd.DataFrame(predictions).copy()
    outcome_by_patient = {str(row["patient_id"]): row for row in outcomes}
    labels = []
    horizon = pd.Timedelta(hours=horizon_hours)
    for _, prediction in table.iterrows():
        patient_id = str(prediction["patient_id"])
        anchor = pd.Timestamp(prediction["prediction_at"])
        if anchor.tzinfo is None:
            raise ValueError("prediction_at must be timezone-aware")
        anchor = anchor.tz_convert("UTC")
        outcome = outcome_by_patient[patient_id]
        event = pd.Timestamp(outcome["event_at"]) if outcome.get("event_at") is not None else None
        discharge = pd.Timestamp(outcome["discharge_at"]) if outcome.get("discharge_at") is not None else None
        death = pd.Timestamp(outcome["death_at"]) if outcome.get("death_at") is not None else None
        censor_times = [pd.Timestamp(item).tz_convert("UTC") if pd.Timestamp(item).tzinfo else pd.Timestamp(item).tz_localize("UTC") for item in (discharge, death) if item is not None]
        censor = min(censor_times) if censor_times else None
        if event is not None:
            event = event.tz_convert("UTC") if event.tzinfo else event.tz_localize("UTC")
        if event is not None and event <= anchor:
            label = None
        elif event is not None and event <= anchor + horizon and (censor is None or event <= censor):
            label = 1
        elif censor is None or censor >= anchor + horizon:
            label = 0
        else:
            label = None
        labels.append(label)
    table["label"] = labels
    return table
