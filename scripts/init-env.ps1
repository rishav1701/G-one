$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$target = Join-Path $repo '.env'
$template = Join-Path $repo '.env.example'

function New-DemoSecret {
    $bytes = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

if (-not (Test-Path -LiteralPath $target)) {
    $dbBytes = [byte[]]::new(32)
    $appBytes = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($dbBytes)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($appBytes)
    $dbPassword = [Convert]::ToHexString($dbBytes).ToLowerInvariant()
    $appSecret = [Convert]::ToHexString($appBytes).ToLowerInvariant()
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.AddRange([string[]](Get-Content -LiteralPath $template))
} else {
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.AddRange([string[]](Get-Content -LiteralPath $target))
    $dbPassword = $null
    $appSecret = $null
}

$required = @{
    'POSTGRES_PASSWORD' = $dbPassword
    'APP_SECRET' = $appSecret
}
foreach ($name in $required.Keys) {
    $found = $false
    for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($lines[$index] -match "^$name=(.*)$") {
            $found = $true
            $existingValue = $Matches[1]
            if ([string]::IsNullOrWhiteSpace($existingValue) -or $existingValue -like 'replace-with-generated-*') {
                $value = $required[$name]
                if ([string]::IsNullOrEmpty($value)) { $value = New-DemoSecret }
                $lines[$index] = "$name=$value"
            }
            break
        }
    }
    if (-not $found) {
        $value = $required[$name]
        if ([string]::IsNullOrEmpty($value)) { $value = New-DemoSecret }
        $lines.Add("$name=$value")
    }
}

[System.IO.File]::WriteAllLines($target, [string[]]($lines.ToArray()), [System.Text.UTF8Encoding]::new($false))
Write-Output 'The git-ignored .env file is ready with local database and application secrets.'
