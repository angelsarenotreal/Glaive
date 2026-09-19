import os
import sys
import ctypes
import argparse
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.config import ConfigManager
from src.riot_api import RiotApiClient
from src.game_poller import GamePoller
from src.hotkey_listener import GlobalHotkeyListener
from src.mock_data import get_mock_match_data
from src.ui.overlay_window import GlaiveOverlayWindow
from src.updater import AutoUpdater
from src import __version__


def set_windows_app_user_model_id():
    """Sets explicit AppUserModelID so Windows taskbar groups and pins Glaive as a standalone native app."""
    if sys.platform == "win32":
        try:
            myappid = f"Glaive.ScoutingOverlay.App.{__version__}"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"[Main] Error setting AppUserModelID: {e}")


def main():
    parser = argparse.ArgumentParser(description="Glaive - Ultra-lightweight LoL Scouting Overlay")
    parser.add_argument("--mock", action="store_true", help="Launch in preview mode with mock match data")
    parser.add_argument("--key", type=str, default=None, help="Set Riot Developer API Key")
    parser.add_argument("--region", type=str, default=None, help="Set platform region (e.g. euw1, na1, kr)")
    parser.add_argument("--hidden", action="store_true", help="Start hidden in background waiting for hotkey or game")
    args = parser.parse_args()

    # 1. Windows Taskbar Identity
    set_windows_app_user_model_id()

    # 2. Config initialization
    config_mgr = ConfigManager()
    if args.key:
        config_mgr.update(riot_api_key=args.key)
    if args.region:
        config_mgr.update(default_platform=args.region)
    if args.mock:
        config_mgr.update(mock_mode=True)

    cfg = config_mgr.config

    # 3. Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Glaive")
    app.setApplicationDisplayName("Glaive Overlay")

    # Set App Icon for taskbar & titlebars
    icon_path = os.path.abspath("assets/icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 4. Riot API Client
    api_client = RiotApiClient(cfg)

    # 5. Overlay Window
    overlay = GlaiveOverlayWindow(config_mgr)

    # 6. Background Auto-Updater Check
    updater = AutoUpdater()
    def check_updates_background():
        info = updater.check_for_updates()
        if info:
            overlay.update_available_signal.emit(info)

    update_thread = threading.Thread(target=check_updates_background, daemon=True)
    update_thread.start()

    # 7. Handle Live Match Callbacks
    def on_live_match(raw_players):
        overlay.update_status_signal.emit("● SCOUTING PLAYERS VIA RIOT API...", "LIVE MATCH DETECTED")
        scouted_players = api_client.scout_all_players(raw_players, cfg.default_platform)
        overlay.update_players_signal.emit(scouted_players)
        overlay.update_status_signal.emit("● LIVE MATCH ACTIVE", "SUMMONER'S RIFT · LIVE SCOUTING")
        if not overlay.isVisible():
            overlay.toggle_visibility_signal.emit()

    def on_match_ended():
        overlay.update_status_signal.emit("● WAITING FOR MATCH (PORT 2999)", "LIVE SCOUTING REPORT")

    # 8. Start Game Poller (Port 2999)
    poller = GamePoller(on_match_found=on_live_match, on_match_ended=on_match_ended)
    poller.start()

    # 9. Start Global Hotkey Listener (Ctrl + X)
    def trigger_hotkey():
        overlay.toggle_visibility_signal.emit()

    hotkey_thread = GlobalHotkeyListener(cfg.hotkey, trigger_hotkey)
    hotkey_thread.start()

    # 10. Initial Display State
    if cfg.mock_mode or args.mock:
        mock_players = get_mock_match_data()
        overlay.display_players(mock_players)
        overlay.set_status("● PREVIEW MODE (MOCK DATA)", "PREVIEW · DIAMOND I LOBBY")
    else:
        overlay.set_status("● WAITING FOR MATCH (PORT 2999)", "LIVE SCOUTING REPORT")

    if not args.hidden:
        overlay.show()

    # Clean shutdown handling
    def on_exit():
        poller.stop()
        hotkey_thread.stop()

    app.aboutToQuit.connect(on_exit)

    print(f"[Glaive] App running. Press {cfg.hotkey.upper()} to toggle overlay.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
