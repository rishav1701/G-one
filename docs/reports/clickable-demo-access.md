# Clickable demo access report — 2026-11-13

## Delivered

- Made the Demo clinician and Administrator tiles clickable.
- In localhost development, either tile requests a normal audited server-side session for its selected seeded account. The API accepts only `clinician` or `admin` and retains the existing environment, host, CSRF, and rate-limit checks.
- When the local shortcut is disabled, a tile selects the sign-in context, fills the configured default username, and focuses the password field. It does not fill a password because the application stores only password hashes and the seed password is one-time output.
- Updated frontend and backend tests, API/security documentation, and the README.

## Gate results

- `npm run test -- --run src/app/Login.test.tsx` (from `frontend/`) — passed, 4 tests.
- `npm test` (from `frontend/`) — passed, 22 tests across 5 files.
- `npm run build` (from `frontend/`) — passed, including TypeScript compilation and the Vite bundle.
- `npm run check:raw` and `npm run check:contrast` (from `frontend/`) — passed; all measured token pairs remain above 4.5:1.
- `..\.tools\python311\python.exe -m pytest tests/test_security_spine.py -q -k "not mutating_authenticated_routes_require_session"` (from `backend/`) — passed, 4 tests; the database-backed mutating-route test was excluded because PostgreSQL is unavailable.
- `..\.tools\python311\python.exe -c "import json; from app.main import app; open('../docs/api/openapi.json','w',encoding='utf-8').write(json.dumps(app.openapi(),indent=2)+chr(10))"` (from `backend/`) — passed; refreshed the checked-in API schema.
- `..\.tools\python311\python.exe -m json.tool ..\docs\api\openapi.json > $null` (from `backend/`) — passed; schema is valid JSON.

## UNVERIFIED

- Browser screenshot review at desktop, tablet, and mobile sizes, plus axe checks. The previous local browser attempt timed out.
- PostgreSQL-backed demo sessions. Local database access is unavailable in this session.

## Decision and limitation

- Do not send, store, or expose the demo passwords in the login page. A localhost-only, CSRF-protected server-side session gives judges the same quick access without making hashed passwords retrievable.

## Next verification

- Inspect screenshots and the live seeded demo on a host with the browser and PostgreSQL stack available.
