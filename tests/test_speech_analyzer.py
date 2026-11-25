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

    def test_long_text_without_punctuation_is_wrapped(self):
        segments = split_text_segments("xin chao " * 150)
        self.assertGreater(len(segments), 1)
        self.assertTrue(all(len(part) <= 180 for part in segments))

    def test_abbreviations_and_numbered_lists_are_not_split_off(self):
        self.assertEqual(
            split_text_segments("Tôi sống ở TP. Hồ Chí Minh. Ông A. đến."),
            ["Tôi sống ở TP. Hồ Chí Minh.", "Ông A. đến."],
        )
        self.assertEqual(
            split_text_segments("1. Mở đầu 2. Nội dung"),
            ["1. Mở đầu 2. Nội dung"],
        )

    def test_empty_pause_is_zero(self):
        self.assertEqual(pause_after_segment(""), 0)



if __name__ == "__main__":
    unittest.main()
