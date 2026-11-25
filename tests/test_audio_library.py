import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import audio_library


class AudioLibraryTests(unittest.TestCase):
    def test_sanitize_wav_extension_and_reserved_names(self):
        self.assertEqual(audio_library.sanitize_stem("demo.wav"), "demo")
        self.assertEqual(audio_library.sanitize_stem("CON"), "_CON")
        self.assertEqual(audio_library.sanitize_stem("a/b"), "a_b")

    def test_sanitize_removes_control_characters_and_limits_length(self):
        value = audio_library.sanitize_stem("bad\nname" + "x" * 200)
        self.assertNotIn("\n", value)
        self.assertLessEqual(len(value), 100)

    def test_empty_library_returns_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(audio_library, "OUTPUT_DIR", Path(directory)):
                self.assertEqual(audio_library.list_audio_files(), [])


if __name__ == "__main__":
    unittest.main()
