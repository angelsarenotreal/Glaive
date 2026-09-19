import os
import sys
import ctypes
import argparse
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.config import ConfigManager, set_windows_autostart
from src.asset_manager import get_base_asset_dir
from src.riot_api import RiotApiClient
from src.game_poller import GamePoller
from src.hotkey_listener import GlobalHotkeyListener
from src.mock_data import get_mock_match_data
from src.ui.overlay_window import GlaiveOverlayWindow
from src.ui.tray_icon import GlaiveTrayIcon
from src.ui.hud_prompt import HUDPromptWidget
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
    parser.add_argument("--mock", "--preview", action="store_true", help="Launch in preview mode with mock match data")
    parser.add_argument("--key", type=str, default=None, help="Set Riot Developer API Key")
    parser.add_argument("--region", type=str, default=None, help="Set platform region (e.g. euw1, na1, kr)")
    parser.add_argument("--hidden", "--minimized", action="store_true", help="Start minimized in system tray waiting for game")
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

    # Ensure Windows startup registry is registered if enabled in config
    if sys.platform == "win32" and cfg.start_on_boot:
        set_windows_autostart(True)

    # 3. Qt Application (Resident in tray, zero resources when sleeping)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Glaive")
    app.setApplicationDisplayName("Glaive Overlay")

    # Set App Icon for taskbar & titlebars
    icon_file = get_base_asset_dir() / "icon.png"
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    # 4. Riot API Client
    api_client = RiotApiClient(cfg)

    # 5. Overlay Window (Main 2x5 Scouting Grid)
    overlay = GlaiveOverlayWindow(config_mgr)

    # 6. Top-Center Loading Screen HUD Prompt Banner
    hud_prompt = HUDPromptWidget(hotkey=cfg.hotkey)
    hud_prompt.prompt_clicked.connect(overlay.toggle_visibility_signal.emit)

    # 7. System Tray Icon (Resident in Windows Tray)
    tray_icon = GlaiveTrayIcon()
    tray_icon.show()
    tray_icon.toggle_overlay_requested.connect(overlay.toggle_visibility_signal.emit)
    tray_icon.open_settings_requested.connect(overlay.open_settings)

    def on_tray_mock():
        mock_players = get_mock_match_data()
        overlay.display_players(mock_players)
        overlay.set_status("● PREVIEW MODE (MOCK DATA)", "PREVIEW · GRANDMASTER LOBBY")
        hud_prompt.show_prompt(duration_ms=6000)
        if not overlay.isVisible():
            overlay.show()

    tray_icon.trigger_mock_requested.connect(on_tray_mock)

    # 8. Background Auto-Updater Check
    updater = AutoUpdater()
    def check_updates_background():
        info = updater.check_for_updates()
        if info:
            overlay.update_available_signal.emit(info)
            tray_icon.notify("Update Available", f"Glaive {info.tag_name} is available on GitHub.")

    tray_icon.check_updates_requested.connect(lambda: threading.Thread(target=check_updates_background, daemon=True).start())

    # Initial update check on startup
    threading.Thread(target=check_updates_background, daemon=True).start()

    # Periodic check every 15 minutes
    from PyQt6.QtCore import QTimer
    update_timer = QTimer()
    update_timer.timeout.connect(lambda: threading.Thread(target=check_updates_background, daemon=True).start())
    update_timer.start(15 * 60 * 1000)

    # 9. Handle Live Match Callbacks
    def on_live_match(raw_players):
        overlay.update_status_signal.emit("● SCOUTING PLAYERS VIA RIOT API...", "LIVE MATCH DETECTED")
        tray_icon.notify("Live Match Detected", f"Scouting {len(raw_players)} players on Summoner's Rift...")
        
        # Parallel scout all 10 players
        scouted_players = api_client.scout_all_players(raw_players, cfg.default_platform)
        overlay.update_players_signal.emit(scouted_players)
        overlay.update_status_signal.emit("● LIVE MATCH ACTIVE", "SUMMONER'S RIFT · LIVE SCOUTING")

        # Prompt top-center HUD notification during loading screen
        hud_prompt.show_prompt(duration_ms=10000)

    def on_match_ended():
        hud_prompt.hide_prompt()
        overlay.show_waiting_state()
        overlay.update_status_signal.emit("● WAITING FOR MATCH (PORT 2999)", "LIVE SCOUTING REPORT")

    # 10. Start Game Poller (Port 2999)
    poller = GamePoller(on_match_found=on_live_match, on_match_ended=on_match_ended)
    poller.start()

    # 11. Start Global Hotkey Listener (Ctrl + X)
    def trigger_hotkey():
        hud_prompt.hide_prompt()
        overlay.toggle_visibility_signal.emit()

    hotkey_thread = GlobalHotkeyListener(cfg.hotkey, trigger_hotkey)
    hotkey_thread.start()

    # 12. Initial Display State
    # By default, Glaive starts sleeping quietly in tray until game detected or hotkey pressed
    if args.mock:
        mock_players = get_mock_match_data()
        overlay.display_players(mock_players)
        overlay.set_status("● PREVIEW MODE (MOCK DATA)", "PREVIEW · GRANDMASTER LOBBY")
        overlay.show()
    else:
        overlay.set_status("● WAITING FOR MATCH (PORT 2999)", "LIVE SCOUTING REPORT")
        # Starts sleeping in tray (hidden)
        overlay.hide()

    # Clean shutdown handling
    def on_exit():
        poller.stop()
        hotkey_thread.stop()
        hud_prompt.hide()
        tray_icon.hide()

    app.aboutToQuit.connect(on_exit)

    print(f"[Glaive] App running resident in system tray. Press {cfg.hotkey.upper()} to toggle overlay.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
