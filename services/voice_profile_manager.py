"""Access and validate the editable Voice Profile catalog.

Unknown identity traits and capabilities remain unset until verified.
"""
import json
import logging
import os
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from services.voice_manager import LANGUAGES

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = PROJECT_DIR / "configs" / "voice_profiles.json"
EVALUATION_PATH = PROJECT_DIR / "data" / "voice_evaluations.json"
VALID_EVALUATION_STATUSES = {"pending", "reviewed", "needs_retest"}
_ALLOWED_RATINGS = {"distinctiveness", "naturalness", "rhythm", "expressiveness"}


def _load_profiles():
    with PROFILE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported Voice Profile schema version.")
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Voice Profile catalog must contain a profiles list.")
    seen = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError("Every Voice Profile entry must be an object.")
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
        evaluation = profile.get("evaluation", {})
        if not isinstance(evaluation, dict) or evaluation.get("status") not in VALID_EVALUATION_STATUSES:
            raise ValueError(f"Invalid evaluation status for {voice_id}.")
    return data


def _backup_corrupt_evaluations():
    if not EVALUATION_PATH.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = EVALUATION_PATH.with_name(f"{EVALUATION_PATH.stem}.corrupt.{stamp}.json")
    try:
        shutil.copy2(EVALUATION_PATH, backup)
        logging.warning("Corrupt voice evaluation data backed up to %s", backup)
        return backup
    except OSError:
        logging.exception("Unable to back up corrupt voice evaluation data")
        return None


def _load_saved_evaluations():
    """Load local reviews; preserve malformed user data in a timestamped backup."""
    if not EVALUATION_PATH.exists():
        return {}
    try:
        with EVALUATION_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if (
            not isinstance(data, dict)
            or data.get("schema_version") != 1
            or not isinstance(data.get("evaluations"), dict)
        ):
            raise ValueError("Invalid local voice-evaluation data schema.")
        return data["evaluations"]
    except (json.JSONDecodeError, UnicodeDecodeError, OSError, ValueError):
        logging.exception("Local voice evaluation data is invalid; starting with an empty review set")
        _backup_corrupt_evaluations()
        return {}


def get_voice_profiles(language_code=None):
    profiles = _load_profiles()["profiles"]
    saved = _load_saved_evaluations()
    for profile in profiles:
        key = f"{profile['language']}:{profile['id']}"
        if key in saved and isinstance(saved[key], dict):
            profile["evaluation"].update(saved[key])
    if language_code is not None:
        profiles = [profile for profile in profiles if profile["language"] == language_code]
    return deepcopy(profiles)


def get_voice_profile(voice_id, language_code):
    for profile in get_voice_profiles(language_code):
        if profile["id"] == voice_id:
            return profile
    raise ValueError(f"Voice Profile not found: {language_code}/{voice_id}")


def get_profile_review_summary(language_code=None):
    profiles = get_voice_profiles(language_code)
    reviewed = sum(profile["evaluation"]["status"] == "reviewed" for profile in profiles)
    return {"total": len(profiles), "reviewed": reviewed, "pending": len(profiles) - reviewed}


def save_voice_evaluation(voice_id, language_code, ratings, status="reviewed", notes=""):
    if status not in VALID_EVALUATION_STATUSES:
        raise ValueError(f"Invalid evaluation status: {status}")
    if not isinstance(ratings, dict) or set(ratings) - _ALLOWED_RATINGS:
        raise ValueError("Unsupported evaluation field.")
    normalized_ratings = {}
    for field in _ALLOWED_RATINGS:
        value = ratings.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5
        ):
            raise ValueError(f"{field} must be an integer from 1 to 5 or None.")
        normalized_ratings[field] = value
    if not isinstance(notes, str):
        raise ValueError("Evaluation notes must be text.")
    known_profiles = _load_profiles()["profiles"]
    target = next(
        (profile for profile in known_profiles
         if profile["id"] == voice_id and profile["language"] == language_code),
        None,
    )
    if target is None:
        raise ValueError(f"Voice Profile not found: {language_code}/{voice_id}")
    evaluation = {
        **normalized_ratings,
        "status": status,
        "notes": notes.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds") if status == "reviewed" else None,
    }
    saved = _load_saved_evaluations()
    saved[f"{language_code}:{voice_id}"] = evaluation
    EVALUATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = EVALUATION_PATH.with_suffix(".json.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump({"schema_version": 1, "evaluations": saved}, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_path, EVALUATION_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)
    target["evaluation"].update(evaluation)
    return deepcopy(target)
