# AI Voice Studio

AI Voice Studio is a local desktop text-to-speech application built with Python and Tkinter. The current catalog contains 14 Vietnamese voices and 6 English voices, with speech-style presets, expression-based pauses, voice preview, an audio library, and local voice evaluations.

## Requirements

- Windows 10/11 or a recent Linux distribution
- Python 3.12
- Git (including Git submodule support)
- Internet access for the first model download

The Vietnamese engine is installed from the repository submodule. The English Kokoro engine uses a separate virtual environment so its dependency versions remain isolated from the Vietnamese engine.

## Clone the project

```bash
git clone --branch develop --recurse-submodules https://github.com/Dangkhoi02/AI-Voice_Studio.git
cd AI-Voice_Studio
```

If the project was cloned without submodules:

```bash
git submodule update --init --recursive
```

## Set up environments

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_envs.ps1
.\.venv\Scripts\python.exe app.py
```

Linux:

```bash
bash scripts/setup_envs.sh
.venv/bin/python app.py
```

The English interpreter can be overridden with the `AVS_EN_PYTHON` environment variable if a custom Python installation is required.

## Run tests

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Local data and generated files

- Generated WAV files are stored in `output/`.
- Temporary preview audio is stored in `output/.preview/`.
- Voice evaluations are stored locally in `data/voice_evaluations.json`.
- Rotating diagnostic logs are stored in `logs/app.log`.

These runtime folders are ignored by Git. If the evaluation file is malformed, the application preserves a timestamped backup before continuing with an empty evaluation set.

## Notes

Speech Style currently adjusts the engine's supported speed preset. Expression changes pauses between text segments; it does not change the model's emotional tone or pitch. Auto language detection currently selects one engine for the whole input; mixed Vietnamese-English text is not yet switched sentence by sentence.

The application uses the upstream Kokoro-Vietnamese submodule. Review that project's current license and model terms before redistributing the application or its bundled model assets. Optional integrations are listed separately in `requirements-optional.txt`.

## Test organization

Automated regression tests live in `tests/` and run with `python -m unittest discover -s tests -v`. Older standalone test scripts at the repository root are retained for reference; they are not the canonical test runner.

## Legacy modules

The current desktop application uses the local Kokoro engines in `services/kokoro_service.py` and `services/kokoro_english_service.py`. The older `services/tts_service.py` and `services/gemini_tts.py` files are not part of the active application flow. They are retained as legacy reference code for now; do not assume they are configured or production-ready.
