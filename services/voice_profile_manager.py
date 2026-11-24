"""Access and validate the editable Voice Profile catalog.

Unknown identity traits and capabilities remain unset until verified.
"""
import json
from copy import deepcopy
from pathlib import Path

from services.voice_manager import LANGUAGES


PROJECT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = PROJECT_DIR / "configs" / "voice_profiles.json"
VALID_EVALUATION_STATUSES = {"pending", "reviewed", "needs_retest"}


def _load_profiles():
    with PROFILE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported Voice Profile schema version.")

    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Voice Profile catalog must contain a profiles list.")

    seen = set()
    for profile in profiles:
        language = profile.get("language")
        voice_id = profile.get("id")
        key = (language, voice_id)

        if key in seen:
            raise ValueError(f"Duplicate Voice Profile: {language}/{voice_id}")
        seen.add(key)

        language_data = LANGUAGES.get(language)
        if language_data is None:
            raise ValueError(f"Unknown language in Voice Profile: {language}")

        known_ids = {voice["id"] for voice in language_data["voices"]}
        if voice_id not in known_ids:
            raise ValueError(f"Unknown voice in Voice Profile: {language}/{voice_id}")

        status = profile.get("evaluation", {}).get("status")
        if status not in VALID_EVALUATION_STATUSES:
            raise ValueError(f"Invalid evaluation status for {voice_id}: {status}")

    return data


def get_voice_profiles(language_code=None):
    """Return profiles in catalog order, optionally filtered by language."""
    profiles = _load_profiles()["profiles"]
    if language_code is not None:
        profiles = [
            profile for profile in profiles
            if profile["language"] == language_code
        ]
    return deepcopy(profiles)


def get_voice_profile(voice_id, language_code):
    """Return one profile by language and engine voice ID."""
    for profile in get_voice_profiles(language_code):
        if profile["id"] == voice_id:
            return profile
    raise ValueError(
        f"Voice Profile not found: {language_code}/{voice_id}"
    )


def get_profile_review_summary(language_code=None):
    """Return counts useful for tracking the voice-audition review."""
    profiles = get_voice_profiles(language_code)
    reviewed = sum(
        profile["evaluation"]["status"] == "reviewed"
        for profile in profiles
    )
    return {
        "total": len(profiles),
        "reviewed": reviewed,
        "pending": len(profiles) - reviewed,
    }
