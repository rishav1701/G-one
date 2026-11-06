# Phase 4 report: frontend core

## Result

Phase 4 exit gate: PASS for the implemented routes and seeded scenarios. NO_DATA rendering is verified at the component/state level; the six standard simulator scenarios do not include a no-observation patient, so a live NO_DATA patient journey is not claimed. The app remains a simulated demonstration and is not for clinical use.

## Gate evidence

- Frontend build and strict TypeScript check: `npm run build` passed.
- Frontend unit tests: `npm run test` passed, 18 tests across four files.
- Raw style scan: `npm run check:raw` passed.
- Contrast check: `npm run check:contrast` passed; the lowest measured pair was HIGH at 5.91:1.
- Browser: `npm run test:e2e -- --grep 'Phase 4 routes'` passed, 1 test. The test rendered the routes at 1440×900, 1024×768, and 390×844, checked the simulation banner, no page-level horizontal overflow, and no browser errors. It checked INCOMPLETE and STALE simulator patients, role-disabled observation controls for ADMIN, and the offline notice.
- Screenshots: 24 route/viewport screenshots were saved under `docs/screens/phase-4/`; route review is recorded in `docs/UI_REVIEW.md`.
- Backend: with `DATABASE_URL=postgresql+psycopg://gone:gone@127.0.0.1:5432/gone`, `python -m pytest -q` passed 74 tests with one upstream Starlette deprecation warning. The IPv4 URL was used because the isolated runtime stalled resolving `localhost`; the database accepted direct connections.
- Manual observation form: React Hook Form uses the Zod schema for entry bounds, at-least-one-value validation, and oxygen-status dependency. Existing backend tests assert clinician creation and viewer denial. The browser test asserts ADMIN sees a disabled entry form with the role requirement.
- UI states: shared state component tests cover loading, empty, error, stale, forbidden, and no-data. Badge tests cover LOW, LOW_MEDIUM, MEDIUM, HIGH, INCOMPLETE, STALE, and NO_DATA.

## Implementation notes

- Dashboard and patient directory load clinical records from the API and refresh through TanStack Query.
- Patient monitoring series use per-parameter NEWS2 subscores returned by the backend. The API calculates scores through the NEWS2 domain logic; UI bands are presentation only.
- Observation entry is limited in the UI to CLINICIAN and SENIOR_CLINICIAN, matching the API permission policy. Admin and viewer accounts receive an explicit explanation.
- The Labs tab shows a clear unavailable state because the six-scenario demo has no lab-result fixture.
- The offline notice reports the last successful update rather than implying new data is available.

## UNVERIFIED and limitations

- Docker Compose startup remains unverified.
- A live NO_DATA patient is not part of the standard simulator cohort; rendering is covered by component tests and the explicit no-assessment branch, not by the Phase 4 browser journey.
- Playwright browser testing ran against the local seeded demonstration API; it does not establish clinical suitability.
- A qualified clinician must review NEWS2 before any clinical use. No model prediction is active.

## Commands

Run from `frontend/`:

- `npm run build` — passed.
- `npm run test` — 17 passed.
- `npm run check:raw` — passed.
- `npm run check:contrast` — passed.
- `npm run test:e2e -- --grep 'Phase 4 routes'` — 1 passed.

Run from `backend/` with `DATABASE_URL=postgresql+psycopg://gone:gone@127.0.0.1:5432/gone`:

- `..\.tools\python311\python.exe -m pytest -q` — 74 passed, 1 deprecation warning.

## Next phase

Proceed to Phase 5: alert actions and responses, administration, role-aware navigation, and browser workflow verification.