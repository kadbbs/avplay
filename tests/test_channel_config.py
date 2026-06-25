import json
import tempfile
import unittest
from pathlib import Path

from streamforge.core.channel import load_channels


class ChannelConfigTest(unittest.TestCase):
    def test_load_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "channels.json"
            path.write_text(
                json.dumps(
                    {
                        "channels": [
                            {
                                "name": "demo",
                                "input": "demo.mp4",
                                "hls": True,
                                "publish_rtsp": True,
                                "push_rtmp": "rtmp://localhost/live/demo",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            channels = load_channels(path)
            self.assertEqual(len(channels), 1)
            self.assertEqual(channels[0].name, "demo")
            self.assertTrue(channels[0].publish_rtsp)


if __name__ == "__main__":
    unittest.main()
