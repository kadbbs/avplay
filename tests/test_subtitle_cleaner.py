import unittest

from autosub.core.subtitle_cleaner import (
    apply_offset,
    ensure_min_duration,
    remove_filler_words,
    wrap_subtitle_text,
)
from autosub.models.subtitle_segment import SubtitleSegment


class SubtitleCleanerTest(unittest.TestCase):
    def test_wrap_subtitle_text(self):
        text = "今天我们来讲一下如何使用 FFmpeg 和 Whisper 做一个自动字幕生成工具"
        self.assertIn("\n", wrap_subtitle_text(text, max_chars_per_line=18))

    def test_apply_offset_clamps_zero(self):
        result = apply_offset([SubtitleSegment(1, 0.1, 0.5, "hi")], -1.0)
        self.assertEqual(result[0].start, 0.0)
        self.assertGreater(result[0].end, result[0].start)

    def test_ensure_min_duration_avoids_next_overlap(self):
        segments = [
            SubtitleSegment(1, 0.0, 0.2, "a"),
            SubtitleSegment(2, 0.8, 1.0, "b"),
        ]
        result = ensure_min_duration(segments, 1.0)
        self.assertLessEqual(result[0].end, 0.75)

    def test_remove_filler_words(self):
        self.assertEqual(remove_filler_words("嗯 今天 啊 开始"), "今天 开始")


if __name__ == "__main__":
    unittest.main()
