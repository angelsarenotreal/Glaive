import os
import unittest
import tempfile
from pathlib import Path
from src.config import ConfigManager, AppConfig, PLATFORM_TO_REGION

class TestConfigManager(unittest.TestCase):

    def test_default_config_creation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_path = os.path.join(tmp_dir, "test_config.json")
            mgr = ConfigManager(cfg_path)
            self.assertEqual(mgr.config.default_platform, "euw1")
            self.assertEqual(mgr.config.hotkey, "ctrl+x")
            self.assertEqual(mgr.config.regional_route, "europe")

    def test_config_update_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_path = os.path.join(tmp_dir, "test_config.json")
            mgr = ConfigManager(cfg_path)
            mgr.update(riot_api_key="RGAPI-12345", default_platform="kr", opacity=0.85)

            # Reload
            mgr2 = ConfigManager(cfg_path)
            self.assertEqual(mgr2.config.riot_api_key, "RGAPI-12345")
            self.assertEqual(mgr2.config.default_platform, "kr")
            self.assertEqual(mgr2.config.regional_route, "asia")
            self.assertEqual(mgr2.config.opacity, 0.85)

if __name__ == "__main__":
    unittest.main()
