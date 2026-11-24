"""Access and validate the editable Voice Profile catalog.

Unknown identity traits and capabilities remain unset until verified.
"""
import json
from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path

from services.voice_manager import LANGUAGES


PROJECT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = PROJECT_DIR / "configs" / "voice_profiles.json"
EVALUATION_PATH = PROJECT_DIR / "data" / "voice_evaluations.json"
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


def _load_saved_evaluations():
    """Load user-specific reviews stored outside the versioned voice catalog."""
    if not EVALUATION_PATH.exists():
        return {}
    with EVALUATION_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if data.get("schema_version") != 1 or not isinstance(data.get("evaluations"), dict):
        raise ValueError("Invalid local voice-evaluation data.")
    return data["evaluations"]


def get_voice_profiles(language_code=None):
    """Return catalog profiles with local evaluations overlaid."""
    profiles = _load_profiles()["profiles"]
    saved = _load_saved_evaluations()
    for profile in profiles:
        key = f"{profile['language']}:{profile['id']}"
        if key in saved:
            profile["evaluation"].update(saved[key])
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


def save_voice_evaluation(
    voice_id,
    language_code,
    ratings,
    status="reviewed",
    notes="",
):
    """Persist a listener's evaluation in a local, git-ignored data file."""
    if status not in VALID_EVALUATION_STATUSES:
        raise ValueError(f"Invalid evaluation status: {status}")

    allowed_ratings = {"distinctiveness", "naturalness", "rhythm", "expressiveness"}
    if not isinstance(ratings, dict) or set(ratings) - allowed_ratings:
        raise ValueError("Unsupported evaluation field.")

    normalized_ratings = {}
    for field in allowed_ratings:
        value = ratings.get(field)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise ValueError(f"{field} must be an integer from 1 to 5 or None.")
        normalized_ratings[field] = value

    if not isinstance(notes, str):
        raise ValueError("Evaluation notes must be text.")

    known_profiles = _load_profiles()["profiles"]
    target = next(
        (
            profile for profile in known_profiles
            if profile["id"] == voice_id and profile["language"] == language_code
        ),
        None,
    )
    if target is None:
        raise ValueError(f"Voice Profile not found: {language_code}/{voice_id}")

    evaluation = {
        **normalized_ratings,
        "status": status,
        "notes": notes.strip(),
        "reviewed_at": (
            datetime.now(timezone.utc).isoformat(timespec="seconds")
            if status == "reviewed"
            else None
        ),
    }

    saved = _load_saved_evaluations()
    saved[f"{language_code}:{voice_id}"] = evaluation
    EVALUATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = EVALUATION_PATH.with_suffix(".json.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\\n") as file:
            json.dump(
                {"schema_version": 1, "evaluations": saved},
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\\n")
        os.replace(temporary_path, EVALUATION_PATH)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    target["evaluation"].update(evaluation)
    return deepcopy(target)
