import unittest

from autosub.config import load_style


class ConfigTest(unittest.TestCase):
    def test_load_style(self):
        style = load_style("classic")
        self.assertEqual(style.name, "classic")
        self.assertEqual(style.font_size, 36)


if __name__ == "__main__":
    unittest.main()
