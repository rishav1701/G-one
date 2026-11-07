# Deployment Readiness Check — 2026-11-07

**Status: NOT CONTAINER-VERIFIED. Local demo packaging is configured; no deployment is claimed.**

## Checks completed

- `docker compose config --quiet` passed. Compose resolves `db`, `backend`, and `frontend`; the frontend port binds to `127.0.0.1:8080` by default.
- `.env` contains non-template application and database secrets of at least 32 characters; their values were not printed. `.env` is ignored by Git.
- Frontend production build passed; Vitest: 18 passed; raw style and contrast scans passed.
- PostgreSQL 17.11 was available; backend pytest: 80 passed. One non-failing Starlette `TestClient` deprecation warning was emitted.
- `npm audit --audit-level=moderate`: zero vulnerabilities.
- `pip-audit --local`: no known vulnerabilities among audited dependencies. The local project package `gone-backend` was skipped because it is not published on PyPI.
- Tracked-file secret-pattern fallback: zero matches. Gitleaks is unavailable, so entropy and history scans were not run.

## Unverified / not ready to claim

- Docker Desktop service `com.docker.service` is stopped. `Start-Service` was denied with “Cannot open service”; Docker engine access failed. Image builds, `docker compose up`, container health checks, and the packaged demo workflow could not be verified.
- The Compose stack is a local demonstration setup, not a production deployment configuration. It has no TLS termination, production secret-management integration, backup/restore procedure, high availability, or operational monitoring.
- Qualified clinician review of NEWS2 and clinical governance remain pending. The product remains labelled as simulated and not for clinical use.

## Required next verification

On a Windows account that can start Docker Desktop, start the service and run `scripts/demo.ps1`. Confirm the health endpoint, sign-in, all six simulator scenarios, and `docker compose down`. Only then can the local container deployment gate be marked verified. Public/clinical deployment requires separate infrastructure and governance work.
