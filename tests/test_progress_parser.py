import unittest

from autosub.core.ffmpeg_runner import parse_ffmpeg_time


class ProgressParserTest(unittest.TestCase):
    def test_parse_ffmpeg_time(self):
        self.assertEqual(parse_ffmpeg_time("frame=1 time=00:01:23.45 bitrate=1kbits/s"), 83.45)
        self.assertIsNone(parse_ffmpeg_time("no timestamp"))


if __name__ == "__main__":
    unittest.main()
