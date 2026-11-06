# Security Review

**Review status: PASS for the Phase 7 demo hardening gate.** This is a code and test review of a simulated demonstration, not a certification or clinical security assessment.

## Required controls

| Control | Result | Evidence |
|---|---|---|
| No credentials committed | PASS | Grep fallback scanned tracked files for private-key headers, AWS access keys, GitHub tokens, and certificates; no matches. Hardcoded E2E passwords were removed. Browser passwords are supplied through `E2E_PASSWORD`; temporary accounts and passwords are generated per run. |
| `.env.example` placeholders | DEFERRED to Phase 8 | No `.env.example` exists yet; the packaging phase will add and verify it. No local `.env` file is tracked. |
| CORS restricted to exact frontend origin | PASS | `backend/app/main.py` sets `allow_origins=[settings.frontend_origin]` and does not enable wildcard origins. |
| Security headers | PASS | Middleware sets CSP with `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and a request ID. |
| Parameterized database access and output encoding | PASS | Database writes and reads use SQLAlchemy expressions or static SQL text. No dynamic SQL interpolation or `dangerouslySetInnerHTML` was found in application code. |
| Role matrix, ward scoping, and IDOR | PASS | Backend clinical, alert, and admin tests cover role enforcement and out-of-scope objects. |
| CSRF rejection | PASS | Auth browser test confirms a mutation without the CSRF header receives 403. |
| Login throttling and temporary lockout | PASS | Auth browser test verifies generic credential failures and the lockout message. |
| Session expiry | PASS | Auth browser test expires the database session and confirms redirect to login. |
| Audit append-only | PASS | Simulator/alert tests verify audit rows cannot be updated or deleted. |
| Ingestion idempotency | PASS | Clinical API tests verify duplicate ingestion handling and assessment recomputation. |
| Model loading | PASS | Registry accepts only `models/active`, validates manifest acceptance and artifact hashes, and rejects invalid paths or changed files. No model upload route exists. |
| Pinned dependencies and vulnerability scan | PASS | Direct frontend dependencies and Python requirements are pinned. `npm audit` reports 0 vulnerabilities. `pip-audit --local` reports no known vulnerabilities. |

## Dependency fixes

The npm review initially found 9 advisories (1 moderate, 6 high, 2 critical). Updated React Router, Vitest, Vite, PostCSS, Zod, and the React Hook Form resolver to fixed compatible releases. Zod 4 required the matching resolver update; the frontend build and 18 tests pass afterward. Final `npm audit --audit-level=moderate` reports 0 vulnerabilities.

The Python review initially found advisories in pytest, python-multipart, and Starlette. Updated the pinned versions of FastAPI, Starlette, python-multipart, and pytest; the complete PostgreSQL backend suite passes with the new pins. Final `pip-audit --local` reports no known vulnerabilities. The isolated Python distribution omits its standard-library `venv` module, so local mode was run with a temporary import shim that was deleted immediately after the command.

## Secret scan scope

Gitleaks is not installed. The fallback grep scanned tracked file contents for private-key headers, AWS key IDs, GitHub token formats, and certificate headers and found no matches. The scan did not perform entropy analysis or scan Git history. Playwright secrets are now supplied by environment, and generated test-user passwords are transient.

## Test evidence

- Backend PostgreSQL suite: 79 passed.
- Frontend unit suite: 18 passed.
- Frontend build and TypeScript check: passed.
- Playwright suite: 6 passed, including login/CSRF/session/lockout, the operational workflows, and one seeded journey for each of the six simulator scenarios.
- axe-core: 51 route/viewport scans; zero serious or critical findings.
- Raw style scan and contrast script: passed.

## Remaining review limits

Docker Compose runtime, a clean-clone packaging run, and qualified clinician review remain unverified and are scheduled for release packaging or clinical governance. The application remains a simulated demonstration and is not for clinical use.
