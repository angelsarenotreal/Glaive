import os
import sys
import subprocess
import requests
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Callable
from src import __version__

GITHUB_REPO = "angelsarenotreal/Glaive"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


@dataclass
class ReleaseInfo:
    tag_name: str
    version_tuple: Tuple[int, ...]
    download_url: str
    asset_name: str
    release_notes: str
    published_at: str


def parse_version_string(ver_str: str) -> Tuple[int, ...]:
    """Extracts numeric version tuple from strings like 'v1.0.2', '1.0.0-beta', etc."""
    cleaned = re.sub(r'^[vV]', '', ver_str.strip())
    # Extract only digits separated by dots
    numbers = []
    for part in cleaned.split('.'):
        match = re.match(r'^(\d+)', part)
        if match:
            numbers.append(int(match.group(1)))
        else:
            break
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)


class AutoUpdater:
    """Manages checking for updates, downloading new binaries, and self-updating on Windows."""

    def __init__(self, current_version: str = __version__, repo: str = GITHUB_REPO):
        self.current_version = current_version
        self.current_version_tuple = parse_version_string(current_version)
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"

    def check_for_updates(self) -> Optional[ReleaseInfo]:
        """
        Queries GitHub Releases API to see if a newer version exists.
        Returns ReleaseInfo if update is available, None otherwise.
        """
        try:
            resp = requests.get(
                self.api_url,
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "GlaiveUpdater/1.0"},
                timeout=5
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            tag_name = data.get("tag_name", "")
            remote_ver_tuple = parse_version_string(tag_name)

            if remote_ver_tuple > self.current_version_tuple:
                # Find executable asset (e.g. Glaive.exe)
                assets = data.get("assets", [])
                download_url = ""
                asset_name = ""
                for asset in assets:
                    name = asset.get("name", "")
                    if name.lower().endswith(".exe"):
                        download_url = asset.get("browser_download_url", "")
                        asset_name = name
                        break

                # Fallback to html_url if direct exe is not in assets
                if not download_url:
                    download_url = data.get("html_url", "")
                    asset_name = "GitHub Release Page"

                return ReleaseInfo(
                    tag_name=tag_name,
                    version_tuple=remote_ver_tuple,
                    download_url=download_url,
                    asset_name=asset_name,
                    release_notes=data.get("body", "No release notes provided."),
                    published_at=data.get("published_at", "")
                )
        except Exception as e:
            print(f"[AutoUpdater] Error checking for updates: {e}")

        return None

    def apply_update_windows(
        self,
        download_url: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        Downloads the updated Glaive.exe and executes a self-replacement batch script.
        """
        try:
            is_frozen = getattr(sys, 'frozen', False)
            current_exe = sys.executable if is_frozen else os.path.abspath("Glaive.exe")
            target_dir = os.path.dirname(current_exe)
            new_exe_path = os.path.join(target_dir, "Glaive_update.exe")

            # 1. Download the new binary
            resp = requests.get(download_url, stream=True, timeout=30)
            if resp.status_code != 200:
                return False

            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(new_exe_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent)

            if progress_callback:
                progress_callback(100)

            # If running from source/python rather than frozen exe, simply save the file
            if not is_frozen:
                print(f"[AutoUpdater] Running in source mode. Downloaded updated executable to {new_exe_path}")
                return True

            # 2. Create batch updater script
            bat_path = os.path.join(target_dir, "glaive_updater.bat")
            bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
:retry
del /f /q "{current_exe}" > nul 2>&1
if exist "{current_exe}" (
    timeout /t 1 /nobreak > nul
    goto retry
)
move /y "{new_exe_path}" "{current_exe}" > nul 2>&1
start "" "{current_exe}"
del /f /q "%~f0" > nul 2>&1
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)

            # 3. Launch updater batch script and quit
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                close_fds=True
            )
            sys.exit(0)
            return True

        except Exception as e:
            print(f"[AutoUpdater] Error applying update: {e}")
            return False
