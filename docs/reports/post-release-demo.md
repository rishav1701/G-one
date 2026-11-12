# Post-release demo usability report

**Status: IMPLEMENTATION PREPARED; DATABASE AND BROWSER GATES UNVERIFIED**

## Delivered

- Seed now creates two separate accounts when absent: an unassigned ADMIN for administration and a ward-scoped SENIOR_CLINICIAN for manual observations and clinical actions. Both passwords are generated from environment values or random values and printed only on account creation; repeat seeding preserves existing passwords.
- `scripts/demo.ps1` and `scripts/seed.ps1` reset the simulator before seeding users. The simulator retains its two named ward records across reseeds so existing clinical assignments survive a reset.
- Login explains the clinical account needed for manual entry and the administrator's role restriction.
- The Analytics no-model state distinguishes an inactive ICU research candidate from a deployed ward model and points judges to the model card in the README.
- README adds a judge run-through, the synthetic patient/scenario distinction, and a direct link to the separate ICU research candidate's model card.
- Documented the user's statement that no ward dataset or training resource is available. The ICU research candidate remains inactive and must not be presented as a ward model.

## Gate results

- `npm test` — passed: 5 files, 19 tests.
- `npm run typecheck` — passed.
- `npm run build` — passed. Rollup emitted non-fatal warnings about third-party Zod `@__PURE__` comment placement.
- `npm run check:raw` — passed.
- `npm run check:contrast` — passed; all measured color pairs exceed 4.5:1.
- `..\.tools\python311\python.exe -m py_compile app/seed.py simulator/engine.py tests/test_admin_api.py` (from `backend/`) — passed.
- `..\.tools\python311\python.exe -m pytest -q tests/test_news2.py` — passed: 60 tests.
- `..\.tools\python311\python.exe -m pytest -q tests/test_security_spine.py -k "every_non_allowlisted_route_is_authenticated or health_route_exists"` — passed: 2 tests, 1 deselected.
- `docker compose config --quiet` — passed; `docker compose config --services` listed `db`, `backend`, and `frontend`.
- PowerShell parser check for `scripts/demo.ps1` and `scripts/seed.ps1` — passed.
- SHA-256 checks for the PhysioNet research `model.joblib` and `metrics.json` — both matched the research manifest; `models/active/manifest.json` is absent.

## UNVERIFIED

- The full backend command `..\.tools\python311\python.exe -m pytest -q` was run from `backend/` but stopped during collection: Windows Application Control blocked pandas' native DLL (`ImportError: DLL load failed while importing hashtable`).
- The targeted PostgreSQL-backed seed test in `tests/test_admin_api.py` could not connect to `localhost:5432`; psycopg reported a Windows socket `Permission denied`. The attempted local test-cluster start did not leave a running server. The new seed persistence and role flow therefore need a database-backed rerun.
- No Playwright screenshots, route walkthrough, or axe scan were generated for this patch. The browser binary is present, but the app's local database/API was not reachable. Manual checks are listed in `docs/UI_REVIEW.md`.
- Docker image build and Compose startup remain UNVERIFIED, as in the Phase 8 report.

## Decisions made

- Keep ADMIN unassigned to wards and without clinical actions; add a separate SENIOR_CLINICIAN account so judges can enter observations without weakening RBAC.
- Preserve simulator wards across reseeds so existing ward assignments remain valid.
- Do not train from the simulator or activate the ICU candidate as a ward model because the user has no ward dataset and the ICU cohort/outcome do not match G One.

## Deviations and cut items

- A ward-specific model was not trained or deployed. The user has no dataset/resource, and synthetic scenario data is not acceptable model-training evidence.
- The browser screenshot and PostgreSQL test gates could not be completed in this environment; they are recorded as UNVERIFIED rather than passed.

## Known defects

- Runtime behavior of the new seeded clinician account and manual observation flow was not verified against PostgreSQL in this session.
- A qualified clinician has not reviewed the NEWS2 implementation or local escalation language.

## Next prerequisites

- On a host with a working Docker Engine, run `scripts/demo.ps1`, sign in with the printed `phaseclinician` password, and save a manual observation on `SIM-000003`. Verify that ADMIN cannot save an observation and can still use administration controls.
- Capture and inspect all route screenshots at the three required viewport sizes, run Playwright/axe, and rerun the backend database suite.
- A fit-for-purpose ward model requires an approved adult ward dataset and a complete ward-specific M0 decision with acceptance criteria set before held-out results are viewed.
