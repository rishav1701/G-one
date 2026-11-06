# Local training runbook

## Current safe path: software fixtures only

The checked-in runner accepts only the generated fixture cohort. It rejects `--fixture` omission and does not read files or credentials from an external dataset. The generated candidate, metrics, and model card are software-pipeline evidence only; do not treat them as clinical performance evidence and do not move the artifact to `models/active/`.

From `backend/` with the pinned optional dependencies installed:

```powershell
python -m ml.pipeline.train --fixture --config ml/config.yaml --output ../models/candidate
```

The command runs the shared feature contract and outcome labeller, chronological patient-level train/validation/calibration/test splits, grouped cross-validation on training patients, validation-only model selection (logistic regression and HistGradientBoosting), separate isotonic calibration, and aggregate-only test metrics. It writes `model.joblib`, `manifest.json`, `metrics.json`, calibration data, feature list, model card, configuration snapshot, environment lock, and a data-definition/count fingerprint under `models/candidate/`.

The manifest hashes each artifact and sets `acceptance_passed` to `false`. No active model is loaded by the application. Metrics from this synthetic fixture must never be shown as patient model performance.

## Runtime and resume

`backend/ml/config.yaml` is the single pipeline configuration. `max_train_hours` bounds the candidate search, and the fixed random seeds make fixture runs repeatable. Candidate estimator checkpoints are written under the ignored `.tools/ml-checkpoints/` directory after each completed search candidate. Rerun the same command after interruption to reuse checkpoints with the matching configuration and fixture signature. If either changes, the pipeline starts a new checkpoint set.

Dependency versions are pinned in `backend/requirements-ml.txt` and the generated `environment.lock` records the runtime used for a candidate.

## User-owned data and acceptance criteria

Before a future locally authorized dataset run, the user must complete `docs/DATA_DECISION_RECORD.md`, confirm the dataset's current data-use terms and local data location, specify the cohort/outcome/horizon and observation protocol, and set acceptance criteria before seeing any evaluation result. The current runner intentionally does not ingest that data. A future implementation must add a local-only input adapter with strict schema, provenance, privacy, and split checks before any real-data execution.

The user performs any later extended training run on their own machine. Only aggregate `metrics.json` and manifest output should be shared for review; never share patient-level features, labels, predictions, or row-level artifacts.
