import tempfile
import unittest
from pathlib import Path

from services.tts_manager import (
    create_unique_filename,
    detect_language,
    preview_excerpt,
    generate_audio,
)


class TTSManagerTests(unittest.TestCase):
    def test_detects_accented_vietnamese(self):
        self.assertEqual(detect_language("Xin chào các bạn"), "vi")

    def test_detects_unaccented_vietnamese(self):
        self.assertEqual(detect_language("xin chao cac ban"), "vi")

    def test_french_accents_do_not_force_vietnamese(self):
        self.assertEqual(detect_language("Café résumé naïve"), "en")

    def test_detects_nfd_vietnamese(self):
        self.assertEqual(detect_language("Xin cha\u0300o"), "vi")

    def test_rejects_unsupported_scripts(self):
        with self.assertRaises(ValueError):
            detect_language("こんにちは")

    def test_filename_extension_and_windows_reserved_names(self):
        with tempfile.TemporaryDirectory() as directory:
            path = create_unique_filename("CON.wav", directory)
            self.assertEqual(path.name, "_CON.wav")
            second = create_unique_filename("demo.wav", directory)
            self.assertEqual(second.name, "demo.wav")


    def test_unsupported_language_is_rejected_before_style_lookup(self):
        with self.assertRaisesRegex(ValueError, "Ngôn ngữ"):
            generate_audio("hello", language="fr", style="not-a-style")

    def test_voice_must_belong_to_selected_language(self):
        with self.assertRaisesRegex(ValueError, "không khả dụng"):
            generate_audio("Xin chào", language="vi", voice="af_heart")

    def test_preview_is_limited(self):
        excerpt = preview_excerpt("Xin chào. " + "nội dung " * 100)
        self.assertLessEqual(len(excerpt), 201)
        self.assertTrue(excerpt.endswith("…") or excerpt.endswith("."))


if __name__ == "__main__":
    unittest.main()
