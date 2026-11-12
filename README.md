# G One

G One is a simulated adult-ward deterioration demonstration. It supports clinical judgment; it does not diagnose, prescribe, replace local escalation policy, or provide a paging service.

> **SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.**

NEWS2 must be reviewed by a qualified clinician against the [Royal College of Physicians chart](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/) and local policy before any clinical use. No ward deterioration model is deployed; NEWS2 is the only alert-driving score. Simulator outcomes and fixture metrics are not clinical performance evidence.

A separately trained [PhysioNet ICU sepsis research candidate](docs/PHYSIONET_RESEARCH_RUN.md) is included for hackathon demonstration only. Its [model card and aggregate metrics](models/research/physionet-challenge-2019-sepsis/model_card.md) show a real held-out ICU sepsis experiment; it is inactive and must not be shown as a G One ward estimate. G One has no trained adult-ward model because no suitable ward dataset is available. The six patient scenarios are deterministic software fixtures, not ML training data.

## Quick start — Docker Compose

Use PowerShell from the repository root. Docker Desktop/Engine must be running.

```powershell
.\scripts\init-env.ps1
.\scripts\demo.ps1
```

The setup script creates or updates a git-ignored `.env` with random local database, application, and demo account passwords. The demo script builds and starts PostgreSQL, applies migrations, resets the simulator with seed 42, and creates the two demo accounts. It synchronizes these local demo account passwords from `.env` so the login tiles can populate the credential fields. The default usernames are `phaseadmin` (administration and simulator controls) and `phaseclinician` (patient records, manual observations, and clinical actions). No secret is committed.

Open [http://localhost:8080](http://localhost:8080) and sign in. The health check is [http://localhost:8080/health](http://localhost:8080/health).

### Judge run-through

1. On the local Compose demo, click **Demo clinician** or **Administrator** under Quick demo access. The matching username and password are fetched into the masked sign-in fields; select **Sign in** to continue. The clinician account supports patient records, manual observations, and clinical alert actions. The administrator account supports administration and cannot take clinical actions.
2. Open the dashboard worklist, then select `SIM-000003` to inspect a simulated gradual-deterioration case and its NEWS2 explanation.
3. On the patient page, use **Enter observation** to submit a manual set of observed values. The returned NEWS2 assessment appears on the page. The values remain demonstration input and do not change the model state.
4. Open **Alerts** to review the explanation and history, record a response, and resolve through the confirmation flow.
5. Use the patient directory to inspect `SIM-000007` (missing observations), `SIM-000009` (sensor disconnection), and `SIM-000011` (data-quality scenario). These are fixed simulated cases, not real patients.

The setup script generates local demo passwords into the git-ignored `.env`. Running `scripts/demo.ps1` or `scripts/seed.ps1` synchronizes the local demo account hashes from those values, so an existing local demo database recovers the same credentials. These commands revoke existing sessions for the two demo accounts. The normal seed function preserves account passwords unless this explicit local-demo sync is enabled.

On the loopback-only Docker Compose demo, both quick-access tiles fetch their account's username and password into the sign-in form. Credential retrieval is available only in development for localhost requests, requires CSRF, is rate-limited, and is not cached. Outside that local demo, tiles fill the username only; passwords are never returned by the credential endpoint in production.

Other demo commands:

```powershell
.\scripts\up.ps1
.\scripts\seed.ps1
.\scripts\reset.ps1
docker compose down
```

`up.ps1` starts the services without reseeding. `seed.ps1` resets the simulator and creates the two demo accounts if absent. `reset.ps1` replaces only the synthetic simulator data, preserving users. `docker compose down` stops containers and preserves the local PostgreSQL volume. The Compose file can be syntax-checked without starting Docker:

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
python -m simulator.cli reset-seed --seed 42
python -m app.seed
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`app.seed` creates an ADMIN and a separate SENIOR_CLINICIAN assigned to the simulator wards. It prints each password only when its account is first created. Existing passwords are never changed by reseeding. The simulator should be seeded before the users so the clinical account receives the current ward assignments.

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

Version `v0.1.0` is a local software demonstration release. `docker compose config --quiet`, dependency installation, migrations, seed, simulator scenarios, local API/UI startup, and a clean-clone browser workflow were verified. Docker image builds and Compose runtime were **not verified** because the Docker Desktop service is stopped in this environment and could not be opened by the current Windows account. The exact commands to verify them are the Quick start commands above.
