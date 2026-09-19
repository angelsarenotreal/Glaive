import os
import sys
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


def load_env_file() -> Dict[str, str]:
    """Scans potential directories for .env and returns key-value pairs."""
    env_vars: Dict[str, str] = {}
    search_dirs = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent,
        Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd(),
    ]

    for d in search_dirs:
        env_file = d / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            env_vars[k.strip()] = v.strip().strip('"').strip("'")
            except Exception as e:
                print(f"[Config] Error reading .env: {e}")
            break

    # Apply to os.environ
    for k, v in env_vars.items():
        os.environ[k] = v

    return env_vars


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
        self.env_vars = load_env_file()

        if config_path:
            self.config_file = Path(config_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.config_file = base_dir / "config.json"

        self.config: AppConfig = self.load()

    def load(self) -> AppConfig:
        env_key = os.environ.get("RIOT_API_KEY") or self.env_vars.get("RIOT_API_KEY", "")
        env_platform = os.environ.get("DEFAULT_PLATFORM") or self.env_vars.get("DEFAULT_PLATFORM", "")

        if not self.config_file.exists():
            cfg = AppConfig()
            if env_key:
                cfg.riot_api_key = env_key
            if env_platform:
                cfg.default_platform = env_platform
            self.save(cfg)
            return cfg

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = AppConfig(**data)
                # If config.json doesn't have an api key, fill from .env
                if not cfg.riot_api_key and env_key:
                    cfg.riot_api_key = env_key
                if env_platform and cfg.default_platform == "euw1":
                    cfg.default_platform = env_platform
                return cfg
        except Exception:
            cfg = AppConfig()
            if env_key:
                cfg.riot_api_key = env_key
            return cfg

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
