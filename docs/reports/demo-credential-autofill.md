# Fixed demo credential report — 2026-11-13

## Delivered

- Set the public demo accounts to `phaseadmin` / `admin321` and `phaseclinician` / `clinical321`.
- Quick-access buttons immediately fill both fields from frontend constants. They do not wait for a status request or fetch a password from the API.
- Removed `/auth/demo-status` and `/auth/demo-credentials`. Sign-in continues through the regular database-backed login, session, CSRF, lockout, and RBAC flow.
- The backend seed synchronizes fixed Argon2 hashes for both accounts. Development Compose startup runs the seed, and `scripts/demo.ps1` runs it after the simulator has created ward assignments.
- Documented that these credentials are public and are only for the simulated demonstration.

## Gate results

- `npm test -- --run` (from `frontend/`) — passed, 21 tests across 5 files. The two button tests confirm immediate field population with the fixed values; the page does not make a demo-status or credential request.
- `npm run build` (from `frontend/`) — passed, including TypeScript compilation and Vite production bundle.
- `..\\.tools\\python311\\python.exe -m py_compile app\\api\\auth.py app\\core\\config.py app\\core\\demo_credentials.py app\\seed.py tests\\test_security_spine.py tests\\test_admin_api.py` (from `backend/`) — passed.
- `..\\.tools\\python311\\python.exe -m pytest tests\\test_security_spine.py -q -k "not mutating_authenticated_routes_require_session"` (from `backend/`) — passed, 4 tests; the database-dependent auth test was excluded.
- `docker compose config --quiet` — passed after the final Compose interpolation adjustment.
- OpenAPI regeneration and JSON validation — passed; removed demo-status and demo-credentials paths are absent from the generated schema.
- `git diff --check` — passed after the final edits.

## UNVERIFIED

- PostgreSQL-backed sign-in with the fixed seeded passwords.
- Browser interaction and screenshots; Docker Desktop's engine was unavailable during this session.

## Decision

- Following the user's explicit preference, remove the slow local account status/password lookup and keep fixed public credentials in the demo UI and seed code. Keep the real database password check and role permissions.

## Deviations and cuts

- No features were cut. Runtime and screenshot verification could not be run because Docker Desktop was unavailable.

## Known defects

- No code defect found in the checks above. Database-backed sign-in remains unverified.

## Next prerequisite

- With Docker Desktop running, execute `docker compose up -d --build` from the repository root. The development backend startup syncs both fixed password hashes without resetting simulator data.

## Security limitation

The fixed credentials are intentionally public in frontend and backend source. PostgreSQL stores only Argon2 hashes, but the shared passwords are not suitable for sensitive or clinical deployments.
