from sklearn.model_selection import GroupKFold


def temporal_patient_splits(rows, config: dict) -> dict[str, list[str]]:
    """Assign whole patients to chronologically ordered train/validation/calibration/test sets."""
    ordered = rows.sort_values("prediction_at").drop_duplicates("patient_id")["patient_id"].astype(str).tolist()
    if len(ordered) < 8:
        raise ValueError("At least eight patients are needed for patient-level splits")
    fractions = config["split"]
    train_end = int(len(ordered) * fractions["train"])
    validation_end = train_end + int(len(ordered) * fractions["validation"])
    calibration_end = validation_end + int(len(ordered) * fractions["calibration"])
    if min(train_end, validation_end-train_end, calibration_end-validation_end, len(ordered)-calibration_end) < 2:
        raise ValueError("Each patient-level split must contain at least two patients")
    return {
        "train": ordered[:train_end],
        "validation": ordered[train_end:validation_end],
        "calibration": ordered[validation_end:calibration_end],
        "test": ordered[calibration_end:],
    }


def grouped_cv_splits(patient_ids, config: dict):
    import numpy as np

    groups = np.asarray(patient_ids, dtype=str)
    n_splits = min(int(config["grouped_cv_folds"]), len(set(groups)))
    if n_splits < 2:
        raise ValueError("Grouped cross-validation needs at least two patients")
    return list(GroupKFold(n_splits=n_splits).split(np.zeros(len(groups)), groups=groups))
