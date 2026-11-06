# Phase 3 report: assessment, alerts, audit and simulator

## Result

Phase 3 exit gate: PASS. Track B M1/M2 fixture gate: PASS. The results verify software behavior on synthetic data only; they do not establish clinical model performance or suitability.

## Gate evidence

- PostgreSQL migration: `python -m alembic current` reported `0003_alerts_simulation (head)`.
- Backend: `python -m pytest -q -p no:cacheprovider` reported 74 passed, 1 upstream Starlette deprecation warning.
- Scenario coverage: simulator tests assert stable no-alert behavior; gradual and sudden deterioration alert outcomes; missing-data INCOMPLETE behavior; disconnected-sensor STALE behavior; and data-quality rejection/idempotency outcomes.
- Simulator determinism: `python -m simulator.cli reset-seed --seed 42` was run twice through the public ingestion API. Both canonical outputs had SHA-256 `947A79ADC5CBE3864807042CF4ADF92470EAE63A73B196AE6636A4AE9328134D`.
- Alerts and audit: tests cover deduplication, in-place level changes, hysteresis, acknowledgement/response/resolution, fake-clock escalation, and rejection of audit-row update/delete.
- Track B: `python -m pytest -q -p no:cacheprovider tests\test_ml_pipeline.py` reported 5 passed. The runbook command `python -m ml.pipeline.train --fixture --config ml/config.yaml --output ../models/candidate` completed and wrote a hash-checked candidate manifest and aggregate-only metrics. `acceptance_passed` is false; the model is not active.
- Training safeguards: fixture tests cover split isolation, future leakage, labelling/censoring, inference/training feature parity, artifact hashes, and aggregate-only output. No credentialed or patient data was accessed.
- Audit: write/read audit behavior and append-only enforcement are covered by tests.

## Implementation notes

- Assessment persistence flushes the accepted observation before selecting the latest valid observations, ensuring the assessment includes the observation that triggered it.
- Operational settings reads are available to clinical roles; writes are restricted to ADMIN and audited.
- Simulator reset retains append-only audit history. Simulator-generated records use synthetic identifiers and are marked simulated.
- The fixture-only training pipeline has no active-model integration or clinical inference route.

## UNVERIFIED and limitations

- Docker Compose service startup is outside this phase gate and remains unverified because the Docker engine is unavailable.
- All ML outputs are generated from software fixtures and are not clinical-performance evidence. M0 data governance decisions and user-run training on an approved, externally held dataset remain pending; neither blocks application work.
- A qualified clinician must review NEWS2 implementation before any clinical use. The product remains a demonstration and is not for clinical use.
- Sixth-scenario edge-case depth and alert cooldown tuning were cut as permitted. Core scenario outcomes were retained.

## Commands

Run from `backend/` with `PYTHONPATH=.` and `DATABASE_URL=postgresql+psycopg://gone:gone@127.0.0.1:5432/gone`:

- `..\.tools\python311\python.exe -m alembic current` — `0003_alerts_simulation (head)`.
- `..\.tools\python311\python.exe -m pytest -q -p no:cacheprovider` — 74 passed.
- `..\.tools\python311\python.exe -m pytest -q -p no:cacheprovider tests\test_ml_pipeline.py` — 5 passed.
- `..\.tools\python311\python.exe -m ml.pipeline.train --fixture --config ml\config.yaml --output ..\models\candidate` — candidate generated with `acceptance_passed=false`.
- `..\.tools\python311\python.exe -m simulator.cli reset-seed --seed 42` (twice) — matching canonical SHA-256 above.

## Next phase

Phase 3 and Track B M1/M2 gates passed. Continue to Phase 4: dashboard, patient directory and detail, observation entry, frontend states and UI review.
