"""Train an inactive research candidate on PhysioNet Challenge 2019.

The source dataset is ICU-only; this artifact is never copied into models/active.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
    confusion_matrix, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / ".tools" / "physionet-challenge-2019" / "training"
OUT = ROOT / ".tools" / "physionet-challenge-2019" / "candidate"
SEED = 1729
VITALS = ["HR", "O2Sat", "Temp", "SBP", "MAP", "DBP", "Resp", "EtCO2"]
DROP = {"SepsisLabel"}

def extract_patient(path: Path):
    frame = pd.read_csv(path, sep="|", na_values=["", "NaN"], low_memory=False)
    if "SepsisLabel" not in frame or not len(frame):
        return None
    labels = pd.to_numeric(frame["SepsisLabel"], errors="coerce").fillna(0).astype(int).to_numpy()
    positive = np.flatnonzero(labels == 1)
    stop = int(positive[0]) if len(positive) else len(frame) - 1
    # Limit positive patients to the first at-risk label, excluding established sepsis follow-up.
    frame = frame.iloc[:stop + 1].copy()
    labels = labels[:stop + 1]
    positions = list(range(0, len(frame), 6))
    if len(frame) - 1 not in positions:
        positions.append(len(frame) - 1)
    if len(positive) and stop not in positions:
        positions.append(stop)
    positions = sorted(set(positions))
    rows = []
    numeric_columns = [c for c in frame.columns if c not in DROP]
    for index in positions:
        row = pd.to_numeric(frame.iloc[index][numeric_columns], errors="coerce").to_dict()
        history = frame.iloc[max(0, index - 5):index + 1]
        for vital in VITALS:
            if vital in frame.columns:
                values = pd.to_numeric(history[vital], errors="coerce").dropna()
                row[f"{vital}_6h_mean"] = float(values.mean()) if len(values) else np.nan
                row[f"{vital}_6h_min"] = float(values.min()) if len(values) else np.nan
                row[f"{vital}_6h_max"] = float(values.max()) if len(values) else np.nan
                row[f"{vital}_6h_delta"] = (float(values.iloc[-1] - values.iloc[0]) if len(values) >= 2 else np.nan)
        rows.append(row)
    labels_sampled = [int(labels[i]) for i in positions]
    ids = [f"{path.parent.name}-{path.stem}"] * len(positions)
    return rows, labels_sampled, ids, int(bool(len(positive)))

def metric(y, p, threshold, patients):
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"n_rows": int(len(y)), "n_patients": int(len(set(patients))),
      "positive_rows": int(np.sum(y)), "prevalence": float(np.mean(y)),
      "auroc": float(roc_auc_score(y, p)), "auprc": float(average_precision_score(y, p)),
      "brier_score_uncalibrated": float(brier_score_loss(y, p)),
      "threshold": float(threshold), "sensitivity": float(tp/(tp+fn)) if tp+fn else None,
      "specificity": float(tn/(tn+fp)) if tn+fp else None,
      "positive_predictive_value": float(tp/(tp+fp)) if tp+fp else None,
      "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}

if __name__ == "__main__":
    if not DATA.exists(): raise SystemExit(f"Dataset directory missing: {DATA}")
    paths = sorted(DATA.glob("training_set*/p*.psv"))
    if not paths: raise SystemExit(f"No patient files found under {DATA}")
    records=[]; targets=[]; groups=[]; patient_positive={}
    for i, path in enumerate(paths, 1):
        extracted=extract_patient(path)
        if extracted is None: continue
        rows, ys, ids, positive=extracted
        records.extend(rows); targets.extend(ys); groups.extend(ids); patient_positive[f"{path.parent.name}-{path.stem}"]=positive
        if i % 2000 == 0: print(f"Processed {i}/{len(paths)} patient files", flush=True)
    X=pd.DataFrame(records).replace([np.inf, -np.inf], np.nan)
    y=np.asarray(targets, dtype=int); groups=np.asarray(groups, dtype=str)
    patient_ids=np.array(sorted(patient_positive)); patient_labels=np.array([patient_positive[x] for x in patient_ids])
    train_ids, hold_ids=train_test_split(patient_ids, test_size=.30, random_state=SEED, stratify=patient_labels)
    hold_labels=np.array([patient_positive[x] for x in hold_ids])
    val_ids, test_ids=train_test_split(hold_ids, test_size=.50, random_state=SEED, stratify=hold_labels)
    train_mask=np.isin(groups, train_ids); val_mask=np.isin(groups, val_ids); test_mask=np.isin(groups, test_ids)
    split_ids=(set(train_ids),set(val_ids),set(test_ids))
    if any(split_ids[i] & split_ids[j] for i in range(3) for j in range(i+1,3)):
        raise ValueError("Patient leakage across splits")
    positive_patients={"train":int(sum(patient_positive[x] for x in train_ids)),"validation":int(sum(patient_positive[x] for x in val_ids)),"test":int(sum(patient_positive[x] for x in test_ids))}
    if min(positive_patients.values()) < 100:
        raise ValueError("At least 100 positive patients are required in each split")
    # Weight each row so long ICU stays do not dominate patient-level contributions.
    unique_groups, group_counts = np.unique(groups, return_counts=True)
    per_patient = dict(zip(unique_groups, 1.0 / group_counts))
    weights=np.fromiter((per_patient[pid] for pid in groups), dtype=float, count=len(groups))
    models={
      "logistic_regression": make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED)),
      "hist_gradient_boosting": make_pipeline(SimpleImputer(strategy="median", add_indicator=True), HistGradientBoostingClassifier(max_iter=120, learning_rate=.08, l2_regularization=2.0, class_weight="balanced", random_state=SEED)),
    }
    fitted={}; validation={}
    for name, model in models.items():
        model.fit(X.loc[train_mask], y[train_mask], **({"histgradientboostingclassifier__sample_weight": weights[train_mask]} if name.startswith("hist") else {}))
        probs=model.predict_proba(X.loc[val_mask])[:,1]
        validation[name]={"auroc":float(roc_auc_score(y[val_mask],probs)),"auprc":float(average_precision_score(y[val_mask],probs))}
        fitted[name]=model
    chosen=max(validation, key=lambda name: validation[name]["auprc"])
    # Exploratory threshold chosen on validation for 80% sensitivity; not a clinical operating point.
    vp=fitted[chosen].predict_proba(X.loc[val_mask])[:,1]
    candidates=np.unique(vp)
    eligible=[t for t in candidates if np.mean(vp[y[val_mask]==1] >= t) >= .80]
    threshold=float(max(eligible)) if eligible else 0.0
    tp=fitted[chosen].predict_proba(X.loc[test_mask])[:,1]
    results=metric(y[test_mask],tp,threshold,test_ids)
    OUT.mkdir(parents=True,exist_ok=True)
    model_path=OUT/"model.joblib"; joblib.dump({"estimator":fitted[chosen],"feature_names":list(X.columns)},model_path)
    metrics={"status":"research_candidate_not_clinically_validated","dataset":"PhysioNet Computing in Cardiology Challenge 2019 v1.0.0","license":"CC BY 4.0","training_population":"Adult ICU stays from training sets A and B; patient-grouped random development split","outcome":"First Challenge SepsisLabel=1 at an hourly landmark; excludes subsequent positive follow-up rows","prediction_horizon_hours":6,"sampling":"One landmark every 6 hours plus first positive landmark; features use current and trailing 6 hourly records only","patient_split":{"train":len(train_ids),"validation":len(val_ids),"test":len(test_ids),"positive_patients":positive_patients,"seed":SEED},"validation_model_comparison":validation,"selected_model":chosen,"test_metrics":results,"threshold_selection":"Validation threshold targeting at least 0.80 sensitivity; exploratory and not clinical","calibrated":False,"limitations":["ICU population; not validated for ward deterioration or NEWS2","Retrospective challenge labels and non-random missingness","Random patient holdout is not temporal or external validation","Repeated landmark metrics are row-weighted; confidence intervals not computed","Research only; do not use for clinical decisions"]}
    metrics_path=OUT/"metrics.json"; metrics_path.write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    manifest={"model_id":"physionet-challenge-2019-sepsis-research","version":"0.1.0","algorithm":chosen,"training_population":"ICU","outcome":"Challenge SepsisLabel","horizon_hours":6,"dataset_version":"PhysioNet Challenge 2019 v1.0.0","license":"CC BY 4.0","acceptance_passed":False,"active":False,"model_sha256":hashlib.sha256(model_path.read_bytes()).hexdigest(),"metrics_sha256":hashlib.sha256(metrics_path.read_bytes()).hexdigest(),"python_version":sys.version.split()[0],"scikit_learn_version":sklearn.__version__}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    card=(
        "# Model Card: PhysioNet Challenge 2019 ICU Sepsis Research Candidate\n\n"
        "Research and hackathon demonstration only. This inactive ICU sepsis model is not clinical decision support, is not prospectively or externally validated, and is not loaded by G One. It is not compatible with G One's ward NEWS2 feature contract.\n\n"
        "Data: PhysioNet/Computing in Cardiology Challenge 2019 v1.0.0 training sets A and B, CC BY 4.0. Attribution: Reyna et al., doi:10.13026/v64v-d857.\n\n"
        f"Selected algorithm: {chosen}. Patient-grouped split: train {len(train_ids)} ({positive_patients['train']} positive), validation {len(val_ids)} ({positive_patients['validation']} positive), test {len(test_ids)} ({positive_patients['test']} positive).\n\n"
        f"Test AUROC: {results['auroc']:.4f}; AUPRC: {results['auprc']:.4f}; prevalence: {results['prevalence']:.4%}; uncalibrated Brier score: {results['brier_score_uncalibrated']:.4f}. At the validation-selected exploratory threshold {threshold:.4f}, sensitivity: {results['sensitivity']:.2%}, specificity: {results['specificity']:.2%}, PPV: {results['positive_predictive_value']:.2%}.\n\n"
        "Limitations: ICU-only, sepsis-specific, random patient holdout, row-weighted repeated-landmark metrics, uncalibrated probabilities, no confidence intervals or subgroup/external/prospective validation. Do not use for clinical decisions or ward/NEWS2 claims."
    )
    (OUT/"model_card.md").write_text(card,encoding="utf-8")
    print(json.dumps({"candidate":str(OUT),"selected_model":chosen,"validation":validation,"test_metrics":results,"manifest_acceptance_passed":False},indent=2),flush=True)
