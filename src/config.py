import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any

# Map platform to regional routing values for Riot Web API
PLATFORM_TO_REGION: Dict[str, str] = {
    # Americas
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    # Europe
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "me1": "europe",
    # Asia
    "kr": "asia",
    "jp1": "asia",
    # SEA
    "oc1": "sea",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}

AVAILABLE_REGIONS = [
    ("EUW (Europe West)", "euw1"),
    ("NA (North America)", "na1"),
    ("EUNE (Europe Nordic & East)", "eun1"),
    ("KR (Korea)", "kr"),
    ("OCE (Oceania)", "oc1"),
    ("BR (Brazil)", "br1"),
    ("LAS (Latin America South)", "la2"),
    ("LAN (Latin America North)", "la1"),
    ("TR (Turkey)", "tr1"),
    ("RU (Russia)", "ru"),
    ("JP (Japan)", "jp1"),
    ("ME (Middle East)", "me1"),
    ("SG (Singapore)", "sg2"),
    ("PH (Philippines)", "ph2"),
    ("TW (Taiwan)", "tw2"),
    ("VN (Vietnam)", "vn2"),
    ("TH (Thailand)", "th2"),
]


@dataclass
class AppConfig:
    riot_api_key: str = ""
    default_platform: str = "euw1"  # e.g., euw1, na1, kr
    hotkey: str = "ctrl+x"
    opacity: float = 0.95
    poll_interval_seconds: float = 2.5
    mock_mode: bool = False
    window_scale: float = 1.0
    compact_mode: bool = False
    always_on_top: bool = True
    click_through: bool = False

    @property
    def regional_route(self) -> str:
        return PLATFORM_TO_REGION.get(self.default_platform.lower(), "europe")


class ConfigManager:
    """Manages reading and writing application configuration safely."""

    def __init__(self, config_path: str | None = None):
        if config_path:
            self.config_file = Path(config_path)
        else:
            # Place in local app directory or user app data
            base_dir = Path(__file__).resolve().parent.parent
            self.config_file = base_dir / "config.json"

        self.config: AppConfig = self.load()

    def load(self) -> AppConfig:
        if not self.config_file.exists():
            cfg = AppConfig()
            # Also check environment variables
            env_key = os.environ.get("RIOT_API_KEY")
            if env_key:
                cfg.riot_api_key = env_key
            self.save(cfg)
            return cfg

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            return AppConfig()

    def save(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self.config = config
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] Error saving config: {e}")

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self.save()
