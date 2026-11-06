# Machine-learning pipeline methodology (fixture verification only)

The M1/M2 implementation shares one feature builder between offline model training and trusted-bundle inference. The prediction-time feature builder filters observations to `measured_at <= prediction_at` before calculating latest values, time since observation, rolling minimum/maximum/mean/slope/count, missingness indicators, NEWS2 breakdown, age, and sex features.

The outcome labeller applies a configured future horizon, excludes events at or before prediction time, and treats discharge or death before the end of the horizon as censoring. Patient IDs are assigned to non-overlapping chronological train, validation, calibration, and test partitions. Grouped cross-validation runs within training patients only. Hyperparameter selection uses validation average precision; isotonic calibration is fitted on a separate calibration split; the held-out test split is evaluated once after selection.

Reference NEWS2, logistic regression, and HistGradientBoosting use the same fixture cohort and outcome horizon. Metrics include AUROC, AUPRC and prevalence, sensitivity, specificity, positive predictive value, calibration slope/intercept and plot bins, Brier score, patient-bootstrap confidence intervals, alerts per patient-day at the closest attainable sensitivity to the configured NEWS2 reference, lead-time summary, and age/sex subgroup counts and metrics.

**All current outputs are generated from synthetic software fixtures. They are not clinical performance evidence.** The candidate manifest is hard-coded to `acceptance_passed: false`; no acceptance criteria have been supplied, no model is deployed, and NEWS2 remains the only alert-driving score. No credentialed patient data has been read by this pipeline.

## Application integration (M5)

The application inspects only `models/active/`. It rejects an artifact unless the manifest is complete, `acceptance_passed` is exactly `true`, every referenced file matches its SHA-256, the shared feature-contract version matches, and the verified metrics/config/model bundle can be loaded. Candidate artifacts are never searched or loaded. The current active directory is empty, so Analytics and patient Overview show the no-model state.

For an accepted active artifact, inference uses the same prediction-time feature builder as training. Each NEWS2 assessment receives at most one stored model prediction per model ID and version. Predictions are secondary to NEWS2, are tagged as interface demonstrations for simulated admissions, and are never used to create NEWS2 alerts. If an artifact is removed or fails verification, its stored predictions are not returned by the API. Metrics are displayed only from the verified artifact's aggregate metrics file.

Automated integration uses a clearly marked temporary software test artifact outside `models/active/`; it is not a candidate for promotion and its test metrics are not shown in the application. The app's production no-model state is tested with the actual empty `models/active/` directory.
