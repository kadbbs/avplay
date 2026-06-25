import unittest

from streamforge.cli import build_parser


class CliTest(unittest.TestCase):
    def test_parse_run_channel(self):
        parser = build_parser()
        args = parser.parse_args(["run-channel", "demo", "demo.mp4", "--hls", "--publish-rtsp"])
        self.assertEqual(args.command, "run-channel")
        self.assertEqual(args.name, "demo")
        self.assertTrue(args.hls)
        self.assertTrue(args.publish_rtsp)


if __name__ == "__main__":
    unittest.main()
