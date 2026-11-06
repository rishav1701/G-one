# Model Card — No Deployed Model

## Current status

No trained ML model is deployed. The active registry directory `models/active/` is empty. The application displays the no-model state. NEWS2 remains the only score that can drive alerts.

The fixture-only training pipeline can write an explicitly unaccepted candidate under `models/candidate/`. Fixture metrics are software-pipeline checks and are not displayed as patient model performance. The isolated test artifact used by registry tests is temporary and is not promoted or shipped.

## Intended use

No predictive model has an intended clinical use in this release. G One itself is a simulated decision-support software demonstration for adult ward deterioration workflows. It is not for clinical use and does not replace clinical judgment or local policy.

## Data and evaluation

No real or credentialed patient dataset has been read by the pipeline. There is no approved cohort, outcome definition, prediction horizon, acceptance criteria, clinical calibration, prospective evaluation, or subgroup review. `docs/DATA_DECISION_RECORD.md` must be completed by the data owner before locally authorized training.

## Risks and limitations

The model interface checks artifact acceptance, hashes, contract version, and metric provenance, but these engineering controls do not establish clinical validity. Future model metrics must be aggregate-only, tied to the data source and cohort, and reviewed for calibration, subgroup performance, and population mismatch. Model attribution is not causation.
