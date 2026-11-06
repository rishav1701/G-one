param([int]$Seed = 42)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    docker compose exec -T backend python -m app.seed
    if ($LASTEXITCODE -ne 0) { throw 'Admin seed failed.' }
    docker compose exec -T backend python -m simulator.cli reset-seed --seed $Seed
    if ($LASTEXITCODE -ne 0) { throw 'Simulator seed failed.' }
} finally { Pop-Location }
