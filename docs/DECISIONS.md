# Decisions

- 2026-11-06: Follow the attached G One prompt as the project specification; no product code is written in Phase 0.
- 2026-11-06: Use the prescribed PostgreSQL-backed architecture; local verification is limited because PostgreSQL is absent. Docker is installed, but service availability is not yet verified.
- 2026-11-06: Treat Python, network, Playwright/browser, and gitleaks as unavailable until an executable or service is verified; do not claim their checks passed.
- 2026-11-06: Used an isolated Python 3.11.9 runtime and EDB PostgreSQL 17.11 binaries under ignored .tools to run Phase 1 verification without a machine-wide install; PostgreSQL test cluster is UTF-8.
- 2026-11-06: Removed explicit PostgreSQL enum creation from the first migration because SQLAlchemy creates the enum when the app_user table is created.
- 2026-11-06: Mapped login 401 responses to the same generic credential-failure message while keeping locked-account responses explicit as required by the login UX contract.
- 2026-11-06: Changed the mobile shell header to a three-row grid after the 390 px screenshot review found overflow; the Playwright no-scroll assertion now passes.
- 2026-11-06: Compared the Phase 2 scoring bands with RCP NEWS2 Chart 1; no difference was found, while clinician verification remains required before clinical use.
- 2026-11-06: Kept hard input limits and plausibility ranges configurable through environment settings and labelled them as technical validation bounds, not clinical thresholds.
- 2026-11-06: Set alert level downgrade to two consecutive lower assessments by default, keep returned-to-low alerts open until explicit resolution, and implement escalation as an in-app demonstration record only.
- 2026-11-06: Kept Track B training fixture-only until the user supplies the M0 data-use/location decision and pre-result acceptance criteria; fixture candidates are always marked unaccepted.

- 2026-11-07: Disable manual observation entry for ADMIN and VIEWER in the UI and explain the required clinical role; API role checks remain authoritative. Phase 4 monitoring graphs use server-returned NEWS2 parameter subscores and presentation-only score bands.
- 2026-11-07: Restrict user management, operational controls, audit viewing, system status, and simulator reset/advance to ADMIN; clinical alert actions remain role-authorized by the API.
- 2026-11-07: Freeze simulator assessments until explicit simulated-clock advancement so clinical values and alert states remain deterministic between control actions.
- 2026-11-07: Give horizontally scrollable tables and the observation-entry panel keyboard focus and accessible names after axe-core identified serious keyboard-access findings.
- 2026-11-07: Record the npm audit findings from the required axe-core dependency install for Phase 7 review; do not apply broad or automatic dependency upgrades during Phase 5.
- 2026-11-07: Compute analytics metrics and scenario counts from current database records at request time; label scenario outcomes as demonstration behaviour, not clinical performance.
- 2026-11-07: Mark seeded lab results as simulated and expose them read-only; they are not included in NEWS2 or model scoring.
- 2026-11-07: Load only explicitly accepted artifacts from `models/active` after manifest, hash, configuration, and path checks; candidate artifacts remain inactive.
- 2026-11-07: Keep NEWS2 as the only alert-driving score; model alerting remains disabled unless an accepted verified model is deployed.
- 2026-11-07: Package the demo with Nginx same-origin API proxy and a local-only Compose stack; use generated ignored `.env` secrets and leave the active model directory empty in the shipped container.
- 2026-11-07: Make admin seeding idempotent without changing existing credentials; simulator reset remains an explicit deterministic reseed operation.
- 2026-11-07: Use PhysioNet Challenge 2019 v1.0.0 as a separate CC BY 4.0 ICU sepsis hackathon research source; keep its candidate inactive and out of the G One NEWS2/ward model registry because the population and outcome differ from the product task.
- 2026-11-07: Bind the local Compose demo to loopback by default so startup does not expose the simulated application to the host network; users must deliberately configure a separately secured reverse proxy for remote access.
- 2026-11-12: Seed a separate randomly credentialed SENIOR_CLINICIAN for judge-facing manual entry while keeping ADMIN free of clinical permissions; seed simulator wards before demo users so their assignments stay in scope.
- 2026-11-12: Retain the two simulator ward records during data reseeds so existing ward assignments and manual demo accounts remain valid as new scenarios are generated.
- 2026-11-12: Keep the existing PhysioNet ICU sepsis candidate inactive and do not train a claimed ward model from simulator data, because the user has no ward dataset and the public candidate's cohort and outcome do not match G One.
