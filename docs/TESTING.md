# Testing

Run commands from the repository root unless specified. PostgreSQL is required for integration tests.

## Backend

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://gone:gone@127.0.0.1:5432/gone'
Set-Location backend
..\.tools\python311\python.exe -m pytest -q
```

## Frontend

```powershell
Set-Location frontend
npm ci
npm run build
npm test
npm run check:raw
npm run check:contrast
```

The browser suite requires the local backend at port 8000 and a seeded administrator. Set `E2E_USERNAME` and `E2E_PASSWORD` in the current PowerShell session to the credentials printed by the seed step, then run `npm run test:e2e` from `frontend/`. Playwright uses Microsoft Edge and runs the main workflows, axe-core checks, viewport fit assertions, scenario journeys, and auth failure-path checks.

## Demo scenario assertions

From `backend/`, after migrations:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://gone:gone@127.0.0.1:5432/gone'
$env:ENVIRONMENT = 'development'
..\.tools\python311\python.exe -m simulator.cli reset-seed --seed 42
```

The deterministic simulator drives stable, deterioration, sudden-change, missing-observation, disconnected-sensor, and data-quality cases through the public observation API. It checks the expected assessment and rejection outcomes and prints a deterministic output hash.

## Phase evidence

Per-phase commands and results are in `docs/reports/phase-*.md`; UI screenshots and route/viewport results are in `docs/UI_REVIEW.md`.
