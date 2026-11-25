import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import voice_profile_manager as profiles


class VoiceProfileManagerTests(unittest.TestCase):
    def test_catalog_contains_all_supported_voices(self):
        records = profiles.get_voice_profiles()
        from services.voice_manager import LANGUAGES
        expected = sum(len(item["voices"]) for item in LANGUAGES.values())
        self.assertEqual(len(records), expected)
        self.assertEqual(profiles.get_profile_review_summary()["total"], expected)

    def test_save_evaluation_persists_scores_and_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_file = Path(directory) / "voice_evaluations.json"
            with patch.object(profiles, "EVALUATION_PATH", temporary_file):
                result = profiles.save_voice_evaluation(
                    "diem_trinh", "vi",
                    {"distinctiveness": 4, "naturalness": 5, "rhythm": 3, "expressiveness": 2},
                    status="reviewed", notes="Giọng rõ và tự nhiên",
                )
                self.assertEqual(result["evaluation"]["naturalness"], 5)
                loaded = profiles.get_voice_profile("diem_trinh", "vi")
                self.assertEqual(loaded["evaluation"]["notes"], "Giọng rõ và tự nhiên")
                self.assertEqual(profiles.get_profile_review_summary("vi")["reviewed"], 1)

    def test_invalid_rating_is_rejected(self):
        with self.assertRaises(ValueError):
            profiles.save_voice_evaluation(
                "diem_trinh", "vi", {"naturalness": 6}
            )


    def test_corrupt_evaluation_file_is_backed_up(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_file = Path(directory) / "voice_evaluations.json"
            temporary_file.write_text("{broken", encoding="utf-8")
            with patch.object(profiles, "EVALUATION_PATH", temporary_file):
                self.assertEqual(profiles._load_saved_evaluations(), {})
            backups = list(Path(directory).glob("voice_evaluations.corrupt.*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "{broken")

    def test_unknown_voice_is_rejected(self):
        with self.assertRaises(ValueError):
            profiles.save_voice_evaluation("unknown", "vi", {})


if __name__ == "__main__":
    unittest.main()
