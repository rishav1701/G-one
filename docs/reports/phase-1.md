# Phase 1 report — Foundation, security spine, design system

## Delivered

- FastAPI service, structured request identifiers, security headers, uniform error envelopes, PostgreSQL connection, and production secret guard.
- SQLAlchemy security-spine models and Alembic migration for ward, app_user, user_ward, session, api_key, system_config, and audit_log.
- Argon2id password hashes; 256-bit opaque server-side sessions stored by hash; httpOnly SameSite=Lax session cookies; Secure cookies outside development; login CSRF challenge; mutation CSRF checks; idle and absolute session expiry; IP throttling; lockout; password change; logout; generated-password seed command.
- Deny-by-default session dependency, role dependency helper, public-route enumeration test, and backend auth-spine tests.
- React/Vite/strict TypeScript shell and login page with persistent simulation banner, skip link, password visibility toggle, CSRF-aware client, route guard, change-password UI, and shared Button, Dialog, Field, Table, LevelBadge, and six-state StateBlock components.
- Self-hosted Inter fonts, design tokens, Tailwind config, raw-value/contrast checks, and pinned frontend dependency lockfile.
- Playwright tests for browser login, generic wrong-password response, account lockout, missing-CSRF rejection, password rotation, session expiry, and 1440/1024/390 viewport screenshots.
- Updated the responsive header after visual review found overflow at 390 px; screenshot and no-horizontal-scroll reruns pass.

## Gate results

- Backend starts: PASS — Uvicorn reported startup complete at http://127.0.0.1:8000.
- Health endpoint: PASS — GET /health returned status ok while connected to PostgreSQL.
- PostgreSQL migration: PASS — Alembic upgrade head completed on PostgreSQL 17.11; alembic current reports 0001_security_spine (head); all eight expected tables are present.
- Backend tests: PASS — pytest reported 3 passed. Python compileall passed.
- Frontend build and type-check: PASS — npm run build completed and emitted the Vite production bundle.
- Frontend unit tests: PASS — 3 files and 8 tests passed.
- Raw-value scan: PASS.
- Contrast check: PASS — all eight checked pairs are at least 5.91:1.
- Browser login, wrong password, lockout, CSRF rejection, password change, and expiry: PASS — Playwright reported 3 passed.
- UI gate: PASS — login and shell manually reviewed at 1440×900, 1024×768, and 390×844. Screenshots are in docs/screens/phase-1/. No page-level horizontal scroll; docs/UI_REVIEW.md records each item.

## Commands and evidence

- Backend compile: Python 3.11.9 portable runtime, python -m compileall -q app alembic tests — passed.
- Backend tests: python -m pytest -q -p no:cacheprovider — 3 passed.
- Migration: DATABASE_URL=postgresql+psycopg://gone:gone@127.0.0.1:5432/gone; python -m alembic upgrade head — passed.
- Migration state/table check: python -m alembic current and psql \dt — revision at head; eight tables.
- Health: GET http://127.0.0.1:8000/health — status ok.
- Frontend: npm run build — passed; npm run test — 8 passed; npm run check:raw — passed; npm run check:contrast — passed; npm run test:e2e — 3 passed.

## UNVERIFIED

- Docker Desktop engine remains unavailable, but the Phase 1 gate was verified against a real local PostgreSQL 17.11 server extracted in user space.
- gitleaks was not needed by Phase 1; its availability remains for the hardening phase.

## Decisions

- A temporary portable Python 3.11.9 runtime and EDB PostgreSQL 17.11 binaries were kept under ignored .tools so the gate could run without a machine-wide installation.
- The local PostgreSQL test cluster uses UTF-8 and is initialized under ignored .tools/pgdata-utf8.
- SQLAlchemy creates the PostgreSQL role enum when the first enum-backed table is created; the migration no longer creates that enum twice.
- See docs/DECISIONS.md for the complete decision log.

## Deviations and cut items

None for the Phase 1 exit gate.

## Known defects

No known Phase 1 gate defects. Later product phases will add clinical APIs and replace the current honest empty-dashboard state with persisted worklists.

## Next phase prerequisites

Phase 1 gate passed. Phase 2 may proceed using the supplied NEWS2 specification; clinical methodology must retain its clinical-review notice and official-source comparison.
