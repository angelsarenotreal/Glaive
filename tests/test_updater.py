import unittest
from src.updater import parse_version_string, AutoUpdater, ReleaseInfo

class TestAutoUpdater(unittest.TestCase):

    def test_version_parsing(self):
        self.assertEqual(parse_version_string("v1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version_string("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version_string("v2.1"), (2, 1, 0))
        self.assertEqual(parse_version_string("v1.10.4-beta"), (1, 10, 4))

    def test_version_comparison(self):
        current = parse_version_string("1.0.0")
        newer = parse_version_string("v1.0.1")
        older = parse_version_string("v0.9.9")
        same = parse_version_string("v1.0.0")

        self.assertTrue(newer > current)
        self.assertTrue(older < current)
        self.assertEqual(same, current)

    def test_updater_initialization(self):
        updater = AutoUpdater(current_version="1.0.0", repo="angelsarenotreal/Glaive")
        self.assertEqual(updater.current_version_tuple, (1, 0, 0))
        self.assertEqual(updater.repo, "angelsarenotreal/Glaive")

if __name__ == "__main__":
    unittest.main()
