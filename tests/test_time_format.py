import unittest

from autosub.core.subtitle_writer import format_ass_time, format_srt_time, format_vtt_time


class TimeFormatTest(unittest.TestCase):
    def test_format_srt_time(self):
        self.assertEqual(format_srt_time(1.2), "00:00:01,200")
        self.assertEqual(format_srt_time(3661.234), "01:01:01,234")

    def test_format_vtt_time(self):
        self.assertEqual(format_vtt_time(1.2), "00:00:01.200")

    def test_format_ass_time(self):
        self.assertEqual(format_ass_time(1.2), "0:00:01.20")


if __name__ == "__main__":
    unittest.main()
