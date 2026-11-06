param([int]$Seed = 42)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    docker compose exec -T backend python -m simulator.cli reset-seed --seed $Seed
    if ($LASTEXITCODE -ne 0) { throw 'Simulator reset and reseed failed.' }
} finally { Pop-Location }
