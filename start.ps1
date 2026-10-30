$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Missing .venv. Create it with Python and install requirements.txt first.'
}
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
$env:NLTK_DATA = Join-Path $PSScriptRoot 'nltk_data'
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot '.run/tmp') | Out-Null
$env:TEMP = Join-Path $PSScriptRoot '.run/tmp'
$env:TMP = $env:TEMP
& $pythonExe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
