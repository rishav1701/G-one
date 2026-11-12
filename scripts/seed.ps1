param([int]$Seed = 42)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'init-env.ps1')
Push-Location $repo
try {
    docker compose up -d --force-recreate backend
    if ($LASTEXITCODE -ne 0) { throw 'Backend refresh failed.' }
    docker compose exec -T backend python -m simulator.cli reset-seed --seed $Seed
    if ($LASTEXITCODE -ne 0) { throw 'Simulator seed failed.' }
    docker compose exec -T backend python -m app.seed
    if ($LASTEXITCODE -ne 0) { throw 'Demo user seed failed.' }
} finally { Pop-Location }
