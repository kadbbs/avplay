import unittest

from streamforge.core.channel import Channel
from streamforge.core.ffmpeg_commands import (
    build_hls_command,
    build_publish_rtsp_command,
    build_push_rtmp_command,
)


class CommandBuilderTest(unittest.TestCase):
    def test_hls_command_for_rtsp_uses_transport_and_hls_output(self):
        channel = Channel(name="cam1", input="rtsp://example/live")
        command = build_hls_command(channel)
        self.assertIn("-rtsp_transport", command)
        self.assertIn("runtime/hls/cam1/index.m3u8", command)
        self.assertIn("-f", command)
        self.assertIn("hls", command)

    def test_file_input_uses_re(self):
        channel = Channel(name="demo", input="demo.mp4")
        command = build_hls_command(channel)
        self.assertIn("-re", command)

    def test_publish_rtsp_target(self):
        channel = Channel(name="demo", input="demo.mp4", publish_rtsp=True)
        command = build_publish_rtsp_command(channel)
        self.assertEqual(command[-1], "rtsp://127.0.0.1:8554/demo")

    def test_push_rtmp_target(self):
        channel = Channel(name="demo", input="demo.mp4", push_rtmp="rtmp://x/live/demo")
        command = build_push_rtmp_command(channel)
        self.assertEqual(command[-1], "rtmp://x/live/demo")


if __name__ == "__main__":
    unittest.main()
