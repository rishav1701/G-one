# Demo credential autofill report — 2026-11-13

## Delivered

- Clicking either quick-access account tile fetches its configured username and password into the login form. The password stays masked; the user still chooses **Sign in**.
- The local setup script generates only database and application secrets. Stable public development-demo passwords are defined in backend source; PostgreSQL stores only Argon2 hashes. Demo seeding synchronizes those hashes and revokes existing sessions.
- `POST /api/v1/auth/demo-credentials` accepts only the administrator or clinician account, requires a CSRF token, enforces the local development host gate and existing rate limit, repairs an outdated account hash when necessary, audits sync/fetch without logging credential values, and sends `Cache-Control: no-store`.
- Removed the previous demo-session bypass route; the user now submits the regular username/password login form.
- Outside localhost development, tiles fill only the username. The credential endpoint rejects production and remote requests.

## Gate results

- `npm test -- --run` (from `frontend/`) — passed, 22 tests across 5 files.
- `npm run build` (from `frontend/`) — passed, including TypeScript compilation and Vite production bundle.
- `..\\.tools\\python311\\python.exe -m py_compile app\\api\\auth.py app\\core\\config.py app\\core\\demo_credentials.py app\\seed.py tests\\test_admin_api.py` (from `backend/`) — passed.
- `..\\.tools\\python311\\python.exe -m pytest tests\\test_security_spine.py -q -k "not mutating_authenticated_routes_require_session"` (from `backend/`) — passed, 4 tests; database-backed route test excluded.
- `docker compose config --quiet` — passed; configuration parsed without starting containers.
- Temporary-directory run of `scripts/init-env.ps1` — passed; it generated database/application secrets once, did not generate demo passwords, and preserved generated values on rerun.
- PowerShell parser checks for `scripts/init-env.ps1`, `scripts/demo.ps1`, and `scripts/seed.ps1` — passed.
- `git diff --check` — passed.
- `npm run check:raw` and `npm run check:contrast` (from `frontend/`) — passed; all measured token pairs remain above 4.5:1.
- `..\.tools\python311\python.exe -m pytest tests/test_security_spine.py -q -k "not mutating_authenticated_routes_require_session"` (from `backend/`) — passed, 4 tests; one database-backed test was excluded because PostgreSQL is unavailable.
- `..\.tools\python311\python.exe -m py_compile app/api/auth.py app/seed.py tests/test_security_spine.py tests/test_admin_api.py` (from `backend/`) — passed.
- `..\.tools\python311\python.exe -c "import json; from app.main import app; open('../docs/api/openapi.json','w',encoding='utf-8').write(json.dumps(app.openapi(),indent=2)+chr(10))"` (from `backend/`) — passed; refreshed the API schema.
- `..\.tools\python311\python.exe -m json.tool ..\docs\api\openapi.json > $null` (from `backend/`) — passed.
- `docker compose config --quiet` — passed with temporary process-level placeholder secrets; no Docker containers were started.
- PowerShell temp-directory check of `scripts/init-env.ps1` — passed; generated required secrets and preserved them on rerun.
- PowerShell parser check of `scripts/init-env.ps1`, `scripts/demo.ps1`, and `scripts/seed.ps1` — passed.
- `rg -n "demo-login|DemoLoginIn|demoLogin" backend frontend/src docs/api/openapi.json` — no obsolete session-bypass route remains.
- `git check-ignore -v .env` — `.env` is ignored by `.gitignore`.
- `git diff --check` — passed.

## UNVERIFIED

- PostgreSQL-backed password synchronization, credential fetch, audit record, and sign-in. The local PostgreSQL service is unavailable to this session.
- Browser screenshots and axe checks at 1440×900, 1024×768, and 390×844. The in-app browser could not open the local server.
- Docker rebuild/restart. `docker info --format '{{.ServerVersion}}'` failed because Docker Desktop's Linux engine pipe is unavailable.

## Security limitation

- Demo passwords are intentionally public constants for the localhost demonstration and are visible in source. The credential endpoint reveals the selected demo password to the browser only in localhost development. Production uses separately supplied seed passwords and remote requests are rejected; do not enable credential retrieval on a hosted deployment.

## Next verification

- Run `scripts/demo.ps1`, click each quick-access tile, verify both fields populate, sign in, and inspect the UI screenshots on the demo host.
