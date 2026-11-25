import unittest

from services.style_manager import get_speech_styles, get_speech_style, get_style_id


class StyleManagerTests(unittest.TestCase):
    def test_styles_are_available_for_both_languages(self):
        self.assertTrue(get_speech_styles("vi"))
        self.assertTrue(get_speech_styles("en"))

    def test_style_label_resolves_for_language(self):
        styles = get_speech_styles("vi")
        self.assertEqual(get_style_id(styles[0]["label"], "vi"), styles[0]["id"])

    def test_incompatible_style_is_rejected(self):
        with self.assertRaises(ValueError):
            get_speech_style("not-a-style", "vi")


if __name__ == "__main__":
    unittest.main()
