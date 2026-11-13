# G One implementation plan

## Architecture

Single FastAPI service, synchronous SQLAlchemy 2 and Alembic over PostgreSQL. Domain scoring and alert rules remain framework-independent. React 18, strict TypeScript and Vite frontend calls the versioned API and polls through TanStack Query. A deterministic simulator submits via the machine ingestion API. Track B provides a config-driven training pipeline and verified model registry; NEWS2 remains the only alert-driving score. Docker Compose packages the local demonstration.

## API route inventory (planned; exact request/response shapes to be documented with implementation)

All routes use `/api/v1`. Authentication: session login/logout/current user/password change; clinical and admin routes are authenticated and permission checked. Health is the sole intentional unauthenticated route. Machine ingestion uses a scoped API key.

- `/health` — liveness, no user session.
- `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/password` — login is public with rate limiting; others require session, mutations require CSRF.
- `/patients`, `/patients/{id}`, `/admissions/{id}`, `/admissions/{id}/observations` — clinical roles read within assigned wards; clinicians and senior clinicians may enter observations; admin has no clinical actions.
- `/ingest/observations`, `/ingest/observations/batch` — simulator machine key; manual entry uses clinician session.
- `/alerts`, `/alerts/{id}`, `/alerts/{id}/acknowledge`, `/alerts/{id}/responses`, `/alerts/{id}/resolve`, `/alerts/{id}/escalate` — clinical roles, ward-scoped; role matrix applied per action.
- `/analytics`, `/labs` — ward-scoped clinical read access.
- `/admin/users`, `/admin/settings`, `/admin/status`, `/admin/audit`, `/admin/simulator` — ADMIN only except operational settings read access for clinical roles.

## Database tables

ward, app_user, user_ward, session, api_key, patient, admission, observation, ingestion_rejection, lab_result, risk_assessment, alert, alert_event, clinical_response, escalation, data_source_status, system_config, model_prediction, audit_log.

## Frontend routes

`/login`; `/dashboard`; `/patients`; `/patients/:id` (Overview, Monitoring, Labs, Alerts/responses tabs); `/alerts`; `/analytics`; `/admin` with users, operational settings, system status, audit, and simulator controls. Route visibility follows roles; API permissions are authoritative.

## Phase order and effort estimates

- 0 Recon and environment — 1.5 h (complete).
- 1 Foundation, auth/security, design system — 3 h.
- 2 Clinical core and ingestion — 3 h.
- 3 Assessment, alerts, audit, simulator — 3 h.
- Track B M1/M2 pipeline — about 3 h after Phase 3; depends on completed M0 record. User-run M3 training occurs outside agent environment and does not block app work.
- 4 Frontend core — 4 h.
- 5 Alert centre and administration — 2.5 h.
- 6 Analytics/labs/model integration — 1.5 h, plus 1 h if a verified model exists.
- 7 Hardening — 3 h.
- 8 Packaging/release — 2 h.

## Inputs needed from user (Track B)

M0: dataset/version; credentialing and data-use status; population; inclusion/exclusion criteria; outcome and timestamp source; prediction horizon; observation window/cadence; prediction times; minimum prediction data; acceptance criteria fixed before test results; cohort mismatch assessment; confirmation the dataset remains outside agent access. M3: user runs the documented long training locally and later supplies aggregate-only `metrics.json` and `manifest.json` for review. No patient-level file is requested.

## Environment and conflicts

See `docs/ENVIRONMENT.md`. Phase gates requiring PostgreSQL, Python, Playwright/Chromium, network or gitleaks are not currently verifiable. Docker is installed; daemon and compose workload remain unverified. Use explicit UNVERIFIED labels and prescribed fallbacks. No conflict changes the architecture; Phase 1 may proceed only with honest gate reporting and cannot claim PostgreSQL/browser checks.

## Post-release hackathon usability follow-up

### Findings and scope

- The released seed creates only an ADMIN login, while the authorization rules correctly block admins from clinical entry. Create a separate random-password SENIOR_CLINICIAN demo login with access to the simulator wards, and print its credentials only when it is first created.
- The login screen and quick start do not tell a judge which account supports clinical actions. Add terse login guidance and a judge run-through to the README.
- The user requested convenient local demo access without bypassing normal login. Keep account passwords in masked form fields and submit through the existing authentication flow.
- Follow-up: make clinician and administrator quick-access tiles load both fields from the localhost development endpoint. The selected stable demo password is public by design; PostgreSQL stores only its Argon2 hash.
- Latest user direction: clicking a local-demo tile should fill both fields reliably using stable seeded accounts, rather than generating new credentials on each setup. Use public development-only password constants, store Argon2 hashes in PostgreSQL, synchronize hashes during demo seed or local credential fetch, and keep the CSRF-protected, rate-limited, no-cache endpoint restricted to localhost development. Production requires separately supplied passwords and never exposes this flow.
- Keep the trained PhysioNet 2019 ICU sepsis candidate inactive and accurately labelled. It is not a ward deterioration model, and its metrics must not be presented as G One ward performance.
- Retain the six deterministic simulated scenarios as starter records; manual observations remain possible on those synthetic patients.

### Work order and estimates

1. Update this plan with the post-release scope before product changes (0.1 h).
2. Make seeding idempotently create an unassigned ADMIN and a ward-scoped SENIOR_CLINICIAN with separate generated credentials; run simulator reseed before user seed so ward assignments are current (0.5 h).
3. Add explicit login guidance and update the self-serve demo and manual-entry walkthrough in README (0.4 h).
4. Add a focused PostgreSQL-backed seed/RBAC regression check and run backend/frontend checks (0.5 h).
5. Capture and inspect login and route screenshots at required sizes if a browser/database service is available; record any UI-gate limitation otherwise (0.5 h).
6. Update state, decision record, and a post-release report, then commit the reviewable patch (0.2 h).

### Risks and limits

- Do not assign ADMIN clinical permissions or ship a shared/default demo password.
- Do not activate or show the ICU candidate as a ward model. A genuine ward model requires the user's approved ward dataset decision, target definition, prediction horizon, sampling policy, and acceptance criteria before results are inspected.
- The Docker daemon did not respond during release verification; any container/browser recheck may remain UNVERIFIED.

### Exact user inputs still needed

- User reports having no database or other training-data resource. This blocks training a fit-for-purpose adult ward model. If one becomes available later, record its version and approved data-use status, source/`ML_DATA_DIR`, adult ward population and inclusion/exclusion, outcome event and timestamp source, horizon, observation window/cadence, prediction times, minimum features, and pre-result acceptance criteria. Never upload patient-level data.
- No further input is required for the demo login/manual-entry fix.
