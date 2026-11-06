# Phase 5 report: alert centre and administration

## Result

Phase 5 exit gate: PASS. The real browser workflow exercised administrator account setup, a clinician observation, simulated-time escalation, alert acknowledgement, response recording, resolution, and role restrictions. New routes passed the screenshot review and axe-core check at all three required viewports.

## Delivered

- Added an administrator-only user directory and creation flow with ward assignment, operational settings, system status, read-only audit events, and simulator reset and advance controls.
- Added ADMIN-only API operations for user management, status, audit, wards, and simulator controls. Passwords use Argon2; management actions are audited.
- Completed the alert centre workflow with acknowledgement, response recording, resolution confirmation, live alert age, role-aware actions, and in-app simulated escalation.
- Kept simulated assessments stable until explicit clock advancement, then recomputed them at the simulated time. Manual observation and response timestamps use the simulated clock when active.
- Made scrollable table regions and the observation-entry region keyboard-accessible after the axe gate identified serious findings.
- Added backend coverage for administrative role enforcement and clock-triggered assessment refresh.

## Gate results

- `frontend/`: `npm run build` — passed; strict TypeScript and Vite production build.
- `frontend/`: `npm test` — passed, 18 tests across 4 files.
- `frontend/`: `npm run check:raw` — passed.
- `frontend/`: `npm run check:contrast` — passed. Lowest measured pair: HIGH, 5.91:1.
- `frontend/`: `npm run test:e2e -- --grep 'Phase 5 administration'` — passed, 1 browser test. It covered all five administration tabs, user creation, simulated time advance, escalation, acknowledge/respond/resolve, ADMIN/VIEWER restrictions, and screenshot capture at 1440×900, 1024×768, and 390×844.
- The same Phase 5 Playwright run executed axe-core at each of 18 captured route/viewport combinations: zero serious or critical violations.
- `frontend/`: `npm run test:e2e -- --grep 'Phase 4 routes'` — passed, 1 browser test; rerun after shared accessibility fixes. Its login and clinical route captures also run axe-core at the required sizes.
- `backend/` with `DATABASE_URL=postgresql+psycopg://gone:gone@127.0.0.1:5432/gone`: `..\.tools\python311\python.exe -m pytest -q` — 76 passed, with one upstream Starlette/AnyIO deprecation warning.
- Screenshot evidence: 18 images in `docs/screens/phase-5/`; all six Phase 5 route groups reviewed at the three viewports and recorded in `docs/UI_REVIEW.md`.
- Final simulator reset in the workflow restored the deterministic seed. Temporary `phase5-*` accounts were removed after the test; audit events were retained.

## UNVERIFIED

- Docker Compose startup remains unverified; it is outside this phase's exit gate and remains an open project risk.
- A live NO_DATA patient journey remains unavailable in the six-scenario seed; Phase 4 documents the component/state coverage and limitation.
- `npm install` reported 9 dependency audit findings (1 moderate, 6 high, 2 critical). Dependency audit and remediation are scheduled for Phase 7; no automatic dependency upgrades were applied.

## Decisions

- Administration routes and simulator controls are restricted to ADMIN; clinical alert actions remain limited by clinical role and endpoint authorization.
- Simulator-generated assessment records stay fixed until a user explicitly advances the simulated clock, preserving reproducible demonstrations while allowing deterministic escalation.
- Narrow tables scroll inside a keyboard-focusable, accessibly named region rather than causing page-level horizontal overflow.

## Deviations and cut items

- Audit viewer filtering and account deactivation were cut as explicitly permitted. Audit records are displayed read-only; users can be created and assigned wards.
- Simulator controls implement reset and explicit time advance; scenario selection, pause, and speed controls remain cut from this phase's bounded scope.

## Known defects and prerequisites

- No unresolved Phase 5 gate defect.
- Clinical use remains prohibited pending qualified clinician review of NEWS2. All data is synthetic demonstration data; escalation is an in-app demonstration and is not a paging system.
- Phase 6 can proceed. Docker verification and dependency audit remain for later gates.
