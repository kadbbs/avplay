import tempfile
import unittest
from pathlib import Path

from autosub.core.subtitle_writer import write_srt
from autosub.models.subtitle_segment import SubtitleSegment


class SrtWriterTest(unittest.TestCase):
    def test_write_srt(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "demo.srt"
            write_srt([SubtitleSegment(1, 1.2, 3.8, "大家好")], output)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "1\n00:00:01,200 --> 00:00:03,800\n大家好\n\n",
            )


if __name__ == "__main__":
    unittest.main()
