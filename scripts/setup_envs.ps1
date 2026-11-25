$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path "third_party/Kokoro-Vietnamese")) {
    git submodule update --init --recursive
}

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

py -3.12 -m venv .venv_en
.\.venv_en\Scripts\python.exe -m pip install --upgrade pip
.\.venv_en\Scripts\python.exe -m pip install -r requirements-en.txt

Write-Host "Environments ready. Run: .\.venv\Scripts\python.exe app.py"
