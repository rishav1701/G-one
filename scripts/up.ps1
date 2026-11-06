$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $repo '.env'))) { & (Join-Path $PSScriptRoot 'init-env.ps1') }
Push-Location $repo
try {
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }
} finally { Pop-Location }
