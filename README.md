# G One

G One is a simulated adult-ward deterioration demonstration. It supports clinical judgment; it does not diagnose, prescribe, replace local escalation policy, or provide a paging service.

> **SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.**

NEWS2 must be reviewed by a qualified clinician against the [Royal College of Physicians chart](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/) and local policy before any clinical use. No trained ML model is deployed; NEWS2 is the only alert-driving score. Simulator outcomes and fixture metrics are not clinical performance evidence.

A separately trained [PhysioNet ICU sepsis research candidate](docs/PHYSIONET_RESEARCH_RUN.md) is included for hackathon demonstration only. It is inactive and does not validate ward deterioration or NEWS2.

## Quick start — Docker Compose

Use PowerShell from the repository root. Docker Desktop/Engine must be running.

```powershell
.\scripts\init-env.ps1
.\scripts\demo.ps1
```

The setup script creates a git-ignored `.env` with random local database and application secrets. The demo script builds and starts PostgreSQL, applies migrations, creates the administrator if needed, and resets the simulator with seed 42. On first use, it prints the generated one-time admin password. The default username is `phaseadmin`; the generated password is not saved in the repository.

Open [http://localhost:8080](http://localhost:8080) and sign in. The health check is [http://localhost:8080/health](http://localhost:8080/health).

Other demo commands:

```powershell
.\scripts\up.ps1
.\scripts\seed.ps1
.\scripts\reset.ps1
docker compose down
```

`up.ps1` starts the services without reseeding. `seed.ps1` creates the administrator if absent and resets the simulator. `reset.ps1` replaces only the synthetic simulator data, preserving the administrator. `docker compose down` stops containers and preserves the local PostgreSQL volume. The Compose file can be syntax-checked without starting Docker:

```powershell
docker compose config --quiet
```

## Local development

Use a local PostgreSQL database and set `DATABASE_URL` to its connection string. The following commands are run in separate PowerShell terminals.

Backend terminal:

```powershell
Set-Location backend
python -m pip install ".[ml,test]"
$env:DATABASE_URL = 'postgresql+psycopg://gone:gone@127.0.0.1:5432/gone'
$env:ENVIRONMENT = 'development'
python -m alembic upgrade head
python -m app.seed
python -m simulator.cli reset-seed --seed 42
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`app.seed` prints the one-time administrator password. If that administrator already exists, the seed command leaves its password unchanged.

Frontend terminal:

```powershell
Set-Location frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` to the backend on port 8000.

## Tests and checks

Backend tests require PostgreSQL:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://gone:gone@127.0.0.1:5432/gone'
Set-Location backend
python -m pytest -q
```

Frontend checks:

```powershell
Set-Location frontend
npm run build
npm test
npm run check:raw
npm run check:contrast
```

The Playwright suite expects a seeded admin, PostgreSQL access for its auth-expiry check, and Microsoft Edge:

```powershell
Set-Location frontend
$env:E2E_USERNAME = 'phaseadmin'
$env:E2E_PASSWORD = Read-Host 'Enter the one-time admin password printed by app.seed'
$env:PSQL_PATH = (Get-Command psql).Source
npm run test:e2e
```

## Simulator

The simulator exercises stable observations, gradual deterioration, sudden concerning change, missing observations, sensor disconnection, and data-quality problems. It submits through the public API and asserts its expected system behavior.

```powershell
Set-Location backend
$env:DATABASE_URL = 'postgresql+psycopg://gone:gone@127.0.0.1:5432/gone'
$env:ENVIRONMENT = 'development'
python -m simulator.cli reset-seed --seed 42
```

The command prints the synthetic scenario events and a reproducibility hash. These results are demonstrations of software behavior, not clinical outcomes or performance.

## Documentation

- [Architecture](docs/ARCHITECTURE.md), [Database](docs/DATABASE.md), and [API/OpenAPI](docs/API.md)
- [Clinical methodology](docs/CLINICAL_METHODOLOGY.md), [Data provenance](docs/DATA_PROVENANCE.md), and [Limitations](docs/LIMITATIONS.md)
- [Security review](docs/SECURITY.md), [Testing](docs/TESTING.md), [UI review](docs/UI_REVIEW.md), and [Phase reports](docs/reports/)
- [Model card](docs/MODEL_CARD.md), [ML methodology](docs/ML_METHODOLOGY.md), [training runbook](docs/TRAINING_RUNBOOK.md), and [data decision record](docs/DATA_DECISION_RECORD.md)
- [Future work](docs/FUTURE_WORK.md), [decisions](docs/DECISIONS.md), [project state](docs/STATE.md), and [release notes](docs/RELEASE_NOTES.md)

## Release verification status

Version `v0.1.0` is a local software demonstration release. `docker compose config --quiet`, dependency installation, migrations, seed, simulator scenarios, local API/UI startup, and a clean-clone browser workflow were verified. Docker image builds and Compose runtime were **not verified** because the Docker Desktop engine did not return a server response in the release environment. The exact commands to verify them are the Quick start commands above.
