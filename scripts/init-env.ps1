$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$target = Join-Path $repo '.env'
$template = Join-Path $repo '.env.example'
if (Test-Path -LiteralPath $target) {
    Write-Output '.env already exists; leaving it unchanged.'
    exit 0
}
$dbBytes = [byte[]]::new(32)
$appBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($dbBytes)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($appBytes)
$dbPassword = [Convert]::ToHexString($dbBytes).ToLowerInvariant()
$appSecret = [Convert]::ToHexString($appBytes).ToLowerInvariant()
$lines = Get-Content -LiteralPath $template
$lines = $lines | ForEach-Object {
    if ($_ -like 'POSTGRES_PASSWORD=*') { "POSTGRES_PASSWORD=$dbPassword" }
    elseif ($_ -like 'APP_SECRET=*') { "APP_SECRET=$appSecret" }
    else { $_ }
}
[System.IO.File]::WriteAllLines($target, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output 'Created .env with random database and application secrets. The file is git-ignored.'
