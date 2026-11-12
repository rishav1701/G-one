param([int]$Seed = 42)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $repo '.env'))) { & (Join-Path $PSScriptRoot 'init-env.ps1') }
Push-Location $repo
try {
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri 'http://localhost:8080/health' -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 2 }
    }
    if (-not $ready) { throw 'The G One web service did not become healthy within 120 seconds.' }
    docker compose exec -T backend python -m simulator.cli reset-seed --seed $Seed
    if ($LASTEXITCODE -ne 0) { throw 'Simulator seed failed.' }
    docker compose exec -T backend python -m app.seed
    if ($LASTEXITCODE -ne 0) { throw 'Demo user seed failed.' }
    Write-Output 'Demo is ready at http://localhost:8080. First-run passwords are printed once above.'
} finally { Pop-Location }
