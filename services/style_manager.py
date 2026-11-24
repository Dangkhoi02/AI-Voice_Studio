"""Load and validate speech-style presets for AI Voice Studio."""
import json
from copy import deepcopy
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
STYLE_PATH = PROJECT_DIR / "configs" / "styles.json"
SUPPORTED_LANGUAGES = {"vi", "en"}


def _load_styles():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported speech-style schema version.")

    styles = data.get("styles")
    if not isinstance(styles, list):
        raise ValueError("Speech-style catalog must contain a styles list.")

    seen = set()
    for style in styles:
        style_id = style.get("id")
        if not isinstance(style_id, str) or not style_id.strip():
            raise ValueError("Every speech style must have a non-empty id.")
        if style_id in seen:
            raise ValueError(f"Duplicate speech style: {style_id}")
        seen.add(style_id)

        languages = style.get("languages")
        if not isinstance(languages, list) or not languages:
            raise ValueError(f"Style {style_id} must support at least one language.")
        if not set(languages).issubset(SUPPORTED_LANGUAGES):
            raise ValueError(f"Style {style_id} contains an unsupported language.")

        speed = style.get("speed")
        if not isinstance(speed, (int, float)) or not 0.5 <= speed <= 2.0:
            raise ValueError(f"Style {style_id} has an invalid speed value.")

    return data


def get_speech_styles(language_code=None):
    """Return all styles, optionally filtered by language."""
    styles = _load_styles()["styles"]
    if language_code is not None:
        styles = [
            style for style in styles
            if language_code in style["languages"]
        ]
    return deepcopy(styles)


def get_speech_style(style_id, language_code=None):
    """Return one style by ID, optionally checking language compatibility."""
    for style in get_speech_styles(language_code):
        if style["id"] == style_id:
            return style
    raise ValueError(f"Speech style not found or unsupported: {style_id}")


def get_style_options(language_code):
    """Return display labels for styles available in a language."""
    return [
        style["label"]
        for style in get_speech_styles(language_code)
    ]


def get_style_speed(style_id, language_code=None):
    """Return the speed preset supported by the current TTS interface."""
    return float(get_speech_style(style_id, language_code)["speed"])
