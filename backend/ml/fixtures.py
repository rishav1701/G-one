from datetime import datetime, timedelta, timezone

def synthetic_fixture(patient_count=60):
    """Create deterministic non-clinical records solely for pipeline tests."""
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    patients, observations, predictions, outcomes = [], [], [], []
    for index in range(patient_count):
        patient_id = f"FIX-{index:04d}"
        positive = index % 3 == 0
        anchor = start + timedelta(days=index)
        patients.append({"patient_id": patient_id, "age_years": 30 + (index * 7) % 60,
                         "sex": ("F", "M", "OTHER")[(index + index // 3) % 3]})
        for step, hours_before in enumerate((72, 48, 24, 1)):
            worsening = positive and step >= 2
            observations.append({
                "patient_id": patient_id, "measured_at": anchor - timedelta(hours=hours_before),
                "respiration_rate": int(12 + (4 if worsening else 0) + (index % 3)),
                "spo2": int(97 - (5 if worsening else 0)), "supplemental_o2": False,
                "systolic_bp": int(120 - (15 if worsening else 0)),
                "pulse": int(72 + (30 if worsening else 0) + (index % 5)),
                "consciousness": "ALERT", "temperature": 37.0 + (0.8 if worsening else 0.0),
            })
        predictions.append({"patient_id": patient_id, "prediction_at": anchor, "spo2_scale": 1})
        outcomes.append({
            "patient_id": patient_id,
            "event_at": anchor + timedelta(hours=2) if positive else None,
            "discharge_at": anchor + timedelta(days=2), "death_at": None,
        })
        # Deliberate post-prediction extreme proves the shared features never leak it.
        observations.append({
            "patient_id": patient_id, "measured_at": anchor + timedelta(hours=1),
            "respiration_rate": 99, "spo2": 50, "supplemental_o2": True,
            "systolic_bp": 30, "pulse": 299, "consciousness": "UNRESPONSIVE", "temperature": 44.0,
        })
    return observations, patients, predictions, outcomes
