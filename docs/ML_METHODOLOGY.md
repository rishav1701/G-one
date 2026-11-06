# Machine-learning pipeline methodology (fixture verification only)

The M1/M2 implementation shares one feature builder between offline model training and trusted-bundle inference. The prediction-time feature builder filters observations to `measured_at <= prediction_at` before calculating latest values, time since observation, rolling minimum/maximum/mean/slope/count, missingness indicators, NEWS2 breakdown, age, and sex features.

The outcome labeller applies a configured future horizon, excludes events at or before prediction time, and treats discharge or death before the end of the horizon as censoring. Patient IDs are assigned to non-overlapping chronological train, validation, calibration, and test partitions. Grouped cross-validation runs within training patients only. Hyperparameter selection uses validation average precision; isotonic calibration is fitted on a separate calibration split; the held-out test split is evaluated once after selection.

Reference NEWS2, logistic regression, and HistGradientBoosting use the same fixture cohort and outcome horizon. Metrics include AUROC, AUPRC and prevalence, sensitivity, specificity, positive predictive value, calibration slope/intercept and plot bins, Brier score, patient-bootstrap confidence intervals, alerts per patient-day at the closest attainable sensitivity to the configured NEWS2 reference, lead-time summary, and age/sex subgroup counts and metrics.

**All current outputs are generated from synthetic software fixtures. They are not clinical performance evidence.** The candidate manifest is hard-coded to `acceptance_passed: false`; no acceptance criteria have been supplied, no model is deployed, and NEWS2 remains the only alert-driving score. No credentialed patient data has been read by this pipeline.
