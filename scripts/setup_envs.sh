#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "third_party/Kokoro-Vietnamese" ]]; then
  git submodule update --init --recursive
fi

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

python3.12 -m venv .venv_en
.venv_en/bin/python -m pip install --upgrade pip
.venv_en/bin/python -m pip install -r requirements-en.txt

echo "Environments ready. Run: .venv/bin/python app.py"
