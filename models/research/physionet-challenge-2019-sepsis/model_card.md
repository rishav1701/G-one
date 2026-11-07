# Model Card: PhysioNet Challenge 2019 ICU Sepsis Research Candidate

## Status and intended use

Research and hackathon demonstration only. This is a retrospective ICU sepsis risk model. It is not a clinical decision support model, has not been prospectively or externally validated, and is not approved for patient care. It is not loaded by G One, is not in `models/active`, does not affect NEWS2, and must not be represented as a general ward deterioration model.

## Data and attribution

Trained from PhysioNet/Computing in Cardiology Challenge 2019 v1.0.0 training sets A and B, 40,336 ICU patient files, publicly available under CC BY 4.0. Attribution: Reyna MA, Josef CS, Jeter R, et al. “Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology Challenge.” PhysioNet (2019), doi:10.13026/v64v-d857. The dataset license is included as `LICENSE.txt`.

## Model and target

Histogram gradient boosting selected against logistic regression by validation AUPRC. Challenge SepsisLabel indicates the challenge-defined early sepsis window up to six hours before onset. To reduce post-event leakage, only records through each patient’s first positive label are used. Landmarks are sampled every six hours plus the first positive landmark; features include current numeric measurements and trailing six-hour summaries for the eight vital-sign variables. Training uses patient-balanced weights.

## Evaluation

Deterministic patient-grouped stratified split (seed 1729): train 28,235 patients (2,052 with positive label), validation 6,050 (440 positive), test 6,051 (440 positive). There is no patient overlap. Model selection was on validation AUPRC; the test set was evaluated once after selection.

- Validation AUROC / AUPRC: logistic regression 0.748 / 0.036; histogram gradient boosting 0.836 / 0.098.
- Held-out test AUROC: 0.834.
- Held-out test AUPRC: 0.110 at 0.962% positive landmarks.
- Uncalibrated Brier score: 0.199.
- At the validation threshold selected to target at least 80% sensitivity (0.492), test sensitivity was 81.4%, specificity 72.1%, and PPV 2.75% (358 true positives, 12,651 false positives, 32,656 true negatives, 82 false negatives).

The low PPV means this operating point produces many false alarms. These retrospective metrics do not establish clinical utility.

## Limitations

- ICU care, sepsis-specific labels, two public training cohorts, and a random patient holdout do not match or validate adult ward deterioration, NEWS2, or G One outcomes.
- Missingness is clinically and operationally informative and may differ across hospitals.
- The model is not calibrated; the Brier score and `predict_proba` output must not be interpreted as calibrated clinical risk.
- Row-level metrics count repeated landmarks; confidence intervals and prospective validation were not performed.
- No subgroup fairness assessment or external validation was performed.
- Keep this artifact inactive. It is not compatible with G One’s seven-parameter NEWS2 feature contract.
