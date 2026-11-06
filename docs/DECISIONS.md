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
