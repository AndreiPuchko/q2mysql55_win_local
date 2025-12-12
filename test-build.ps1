.\.venv\Scripts\activate

New-Item -ItemType Directory -Force -Path ./dist

$ProjectName = Split-Path (Get-Location) -Leaf
Write-Host "=== $ProjectName build & release ===" -ForegroundColor Cyan
$VersionPyPath = "$ProjectName/version.py"
$LatestWheelName = "$ProjectName-0-py3-none-any.whl"

$versionFile = "pyproject.toml"
$content = Get-Content $versionFile

$versionLine = $content | Where-Object { $_ -match '^version\s*=' }
if (-not $versionLine) {
    Write-Error "❌ version not found in pyproject.toml"
    exit 1
}

$version = ($versionLine -split '"')[1]
Write-Host "Current version: $version"

function Save-TomlWithoutBOM {
    param (
        [string]$Path
    )

    if (!(Test-Path $Path)) {
        throw "File not found: $Path"
    }

    $content = Get-Content $Path -Raw
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

Save-TomlWithoutBOM "pyproject.toml"

if (Test-Path dist) {
    Remove-Item dist -Recurse -Force
}

python -m build


Copy-Item $ProjectName\version.py dist\version.py -Force
$wheel = Get-ChildItem dist\$ProjectName-*-py3-none-any.whl | Select-Object -First 1
Copy-Item $ProjectName\version.py dist\version.py -Force
$latestFilePath = "dist\latest"
Set-Content -Path $latestFilePath -Value $wheel.Name -Encoding UTF8