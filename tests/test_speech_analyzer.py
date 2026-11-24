import unittest

from services.speech_analyzer import (
    get_expression_id,
    pause_after_segment,
    split_text_segments,
)


class SpeechAnalyzerTests(unittest.TestCase):
    def test_split_keeps_punctuation(self):
        self.assertEqual(
            split_text_segments("Xin chào, bạn khỏe không? Tôi ổn."),
            ["Xin chào,", "bạn khỏe không?", "Tôi ổn."],
        )

    def test_sentence_and_clause_pauses_differ(self):
        self.assertGreater(
            pause_after_segment("Kết thúc.", "gentle"),
            pause_after_segment("Kết thúc.", "enthusiastic"),
        )
        self.assertGreater(
            pause_after_segment("Chào bạn,", "gentle"),
            pause_after_segment("Chào bạn,", "enthusiastic"),
        )

    def test_expression_label_resolves(self):
        self.assertEqual(get_expression_id("Tự nhiên"), "natural")

    def test_empty_text_returns_no_segments(self):
        self.assertEqual(split_text_segments("   "), [])


if __name__ == "__main__":
    unittest.main()
