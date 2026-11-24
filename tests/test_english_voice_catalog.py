import unittest

from services.voice_manager import (
    LANGUAGES,
    get_voice_id,
    get_voice_options,
)
from services.voice_profile_manager import get_voice_profiles
from services.kokoro_english_service import get_kokoro_language_code


class EnglishVoiceCatalogTests(unittest.TestCase):
    def test_keeps_all_fourteen_vietnamese_voices(self):
        self.assertEqual(len(LANGUAGES["vi"]["voices"]), 14)

    def test_registers_six_english_voices(self):
        self.assertEqual(
            {voice["id"] for voice in LANGUAGES["en"]["voices"]},
            {"af_heart", "af_bella", "am_michael", "am_fenrir", "bf_emma", "bm_george"},
        )

    def test_voice_labels_resolve_to_engine_ids(self):
        for voice in LANGUAGES["en"]["voices"]:
            self.assertEqual(
                get_voice_id("en", voice["label"]),
                voice["id"],
            )

    def test_pipeline_code_matches_accent_family(self):
        for voice in LANGUAGES["en"]["voices"]:
            expected = "b" if voice["id"].startswith("b") else "a"
            self.assertEqual(get_kokoro_language_code(voice["id"]), expected)

    def test_invalid_voice_id_is_rejected(self):
        with self.assertRaises(ValueError):
            get_kokoro_language_code("unknown_voice")

    def test_voice_profiles_match_the_catalog(self):
        profiles = get_voice_profiles("en")
        self.assertEqual(
            {profile["id"] for profile in profiles},
            {voice["id"] for voice in LANGUAGES["en"]["voices"]},
        )

    def test_ui_offers_all_english_voices(self):
        options = get_voice_options("en")
        self.assertEqual(len(options), 7)  # Six voices plus automatic selection.


if __name__ == "__main__":
    unittest.main()
