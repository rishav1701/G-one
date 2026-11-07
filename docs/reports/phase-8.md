# Phase 8 Report — Packaging and Release

**Status: COMPLETE WITH DOCKER RUNTIME UNVERIFIED**

## Delivered

- Added `docker-compose.yml` for PostgreSQL, a migrated FastAPI backend, and an Nginx-served frontend with same-origin API proxy and security headers.
- Added backend/frontend Dockerfiles, context ignore rules, `.env.example`, and PowerShell scripts for random secret setup, start, seed, reset, and demo.
- Made admin seeding safe to repeat without changing existing credentials; simulator reset remains a deterministic reseed operation.
- Completed Architecture, Database, API/OpenAPI, Data Provenance, Security, Testing, Limitations, Model Card, Release Notes, and README documentation.
- Added version identifier `v0.1.0`. The released model state is no trained model deployed.

## Gate evidence

- `docker compose config --quiet` — **passed**. `docker compose config --services` lists `db`, `backend`, and `frontend`.
- `git clone --local --no-hardlinks ... .tools/phase8-clone` — clean clone created at commit `1badd32`.
- In the clean clone, `npm ci` — **passed**, 0 npm vulnerabilities.
- In the clean clone, `python -m pip install ".[ml,test]"` — **passed**, wheel built and installed.
- In the clean clone, `alembic upgrade head` — **passed**, migrations 0001 through 0004 applied to a separate PostgreSQL database.
- In the clean clone, `python -m app.seed` and `python -m simulator.cli reset-seed --seed 42` — **passed**. The demo emitted 12 patients in two wards across all six scenarios; stable stayed LOW, gradual/sudden cases escalated, missing data remained INCOMPLETE, sensor disconnection became STALE, and data-quality rejection checks passed. Seed output hash: `cb0943517936cb0fc813a2d290e0fee2c5f265941d3493225020307750ea78a8`.
- In the clean clone, API and Vite development servers started; the Phase 6 Playwright browser workflow logged in and passed analytics, model no-deployment, labs, and axe checks (**1 passed**).
- In the clean clone, backend suite **79 passed**, frontend suite **18 passed**, and frontend production build passed.
- `docs/api/openapi.json` exported from the application with 31 paths.
- Final tracked-file secret grep found no private-key, AWS key, GitHub token, or certificate patterns. `.env` is git-ignored; no secret value was printed in the report.

## UNVERIFIED

- `docker info` and `docker version --format ...` did not return a Docker server response within the bounded probe. Therefore `docker build`, `docker compose up`, container health checks, and the packaged `scripts/demo.ps1` were not run. Compose syntax validation passed.
- Nginx container security headers were reviewed in configuration but could not be inspected in a running container.
- Qualified clinician review of NEWS2 remains pending.

On a host with a responding Docker Desktop/Engine, verify with:

```powershell
.\scripts\init-env.ps1
.\scripts\demo.ps1
Invoke-WebRequest http://localhost:8080/health
.\scripts\reset.ps1
docker compose down
```

## Known limitations

- This is a simulated demonstration and is not for clinical use. No trained model is deployed.
- Docker runtime verification is outstanding. Release notes state this plainly.
- The local Python test run emitted a non-failing Starlette `TestClient` deprecation warning. Pytest also emitted a cache warning in the read-only fresh-clone tree; all 79 tests passed.

## Release

Version: `v0.1.0`. Final release commit recorded by Git history after this report is committed.
