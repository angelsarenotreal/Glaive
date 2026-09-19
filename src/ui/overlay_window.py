import os
import sys
import ctypes
import threading
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QIcon

from src.analytics import PlayerScoutingData
from src.asset_manager import get_base_asset_dir
from src.ui.player_card import PlayerCardWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.theme import MAIN_STYLESHEET
from src.config import ConfigManager
from src.updater import AutoUpdater, ReleaseInfo
from src import __version__

# Win32 Constants for non-activating window
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008

ROLE_SORT_MAP = {
    "TOP": 0,
    "JUNGLE": 1,
    "JGL": 1,
    "MIDDLE": 2,
    "MID": 2,
    "BOTTOM": 3,
    "BOT": 3,
    "ADC": 3,
    "CARRY": 3,
    "AD CARRY": 3,
    "UTILITY": 4,
    "SUPPORT": 4,
    "SUP": 4,
}


def sort_players_by_role(players: List[PlayerScoutingData]) -> List[PlayerScoutingData]:
    """
    Sorts players strictly by Summoner's Rift lane position:
    TOP (0) -> JUNGLE (1) -> MID (2) -> ADC (3) -> SUPPORT (4).
    """
    def role_key(p: PlayerScoutingData) -> int:
        pos = (p.assigned_position or "").upper().strip()
        if pos in ROLE_SORT_MAP:
            return ROLE_SORT_MAP[pos]
        role = (p.main_role or "").upper().strip()
        if "TOP" in role:
            return 0
        if "JUNG" in role or "JGL" in role:
            return 1
        if "MID" in role:
            return 2
        if "CARRY" in role or "ADC" in role or "BOT" in role:
            return 3
        if "SUP" in role or "UTIL" in role:
            return 4
        return 5

    return sorted(players, key=role_key)


class GlaiveOverlayWindow(QWidget):
    """
    Pure 2x5 Player Scouting Grid Overlay Window.
    - Top Row (Row 1): Red Side (Chaos / Map Top)
    - Bottom Row (Row 2): Blue Side (Order / Map Bottom)
    - Left-to-Right Ordering: TOP -> JUNGLE -> MID -> ADC -> SUPPORT
    - Frameless, 100% solid background, sharp 0px corners, non-intrusive.
    """

    toggle_visibility_signal = pyqtSignal()
    update_players_signal = pyqtSignal(list)
    update_status_signal = pyqtSignal(str, str)
    update_available_signal = pyqtSignal(object)

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.cfg = self.config_manager.config
        self.updater = AutoUpdater()
        self.setObjectName("GlaiveOverlay")
        self._current_status = "READY"

        # Window Flags: Frameless, Always On Top, Tool Window
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Set Icon
        icon_file = get_base_asset_dir() / "icon.png"
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))

        # Apply Global Stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Positioning & Dragging
        self.drag_position = QPoint()
        self._is_visible = True
        self._pending_release: Optional[ReleaseInfo] = None

        # Signals
        self.toggle_visibility_signal.connect(self.toggle_overlay)
        self.update_players_signal.connect(self.display_players)
        self.update_status_signal.connect(self.set_status)
        self.update_available_signal.connect(self._on_update_available)

        self.init_ui()
        self.apply_win32_optimizations()

    def apply_win32_optimizations(self):
        """Applies Windows API extended styles to prevent taking keyboard/mouse focus from League."""
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                new_style = current_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            except Exception as e:
                print(f"[Overlay] Error setting Win32 flags: {e}")

    def init_ui(self):
        self.resize(1640, 860)
        self.center_on_screen()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)

        # Main Obsidian Container
        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")
        self.container_layout = QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)

        # ---------------- 0. Update Alert Banner (Hidden unless update available) ----------------
        self.update_banner = QFrame()
        self.update_banner.setStyleSheet(
            "background-color: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); "
            "border-radius: 0px; padding: 4px 8px;"
        )
        self.update_banner.hide()
        banner_layout = QHBoxLayout(self.update_banner)
        banner_layout.setContentsMargins(6, 4, 6, 4)

        self.banner_text = QLabel("A new version of Glaive is available.")
        self.banner_text.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 700;")
        banner_layout.addWidget(self.banner_text)
        banner_layout.addStretch()

        self.update_btn = QPushButton("Update & Restart")
        self.update_btn.setStyleSheet("background-color: #38bdf8; color: #000000; font-weight: 800; padding: 3px 10px; border-radius: 0px;")
        self.update_btn.clicked.connect(self._trigger_update_download)
        banner_layout.addWidget(self.update_btn)

        dismiss_update_btn = QPushButton("✕")
        dismiss_update_btn.setObjectName("IconButton")
        dismiss_update_btn.clicked.connect(self.update_banner.hide)
        banner_layout.addWidget(dismiss_update_btn)

        self.container_layout.addWidget(self.update_banner)

        # ---------------- 1. Waiting State Container (When no active match) ----------------
        self.waiting_container = QFrame()
        self.waiting_container.setStyleSheet("background: transparent; padding: 120px 20px;")
        waiting_layout = QVBoxLayout(self.waiting_container)
        waiting_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waiting_layout.setSpacing(14)

        wait_icon = QLabel("⚔️")
        wait_icon.setStyleSheet("font-size: 38px;")
        wait_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waiting_layout.addWidget(wait_icon)

        wait_title = QLabel("WAITING FOR LEAGUE OF LEGENDS MATCH")
        wait_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 800; letter-spacing: 1.5px;")
        wait_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waiting_layout.addWidget(wait_title)

        wait_subtitle = QLabel("Glaive is sleeping in the background. As soon as you enter a match loading screen, live stats for all 10 players will appear automatically.")
        wait_subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        wait_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waiting_layout.addWidget(wait_subtitle)

        wait_hint = QLabel("Press [ Ctrl + X ] or Esc to toggle this overlay")
        wait_hint.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700; margin-top: 8px;")
        wait_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waiting_layout.addWidget(wait_hint)

        self.container_layout.addWidget(self.waiting_container)

        # ---------------- 2. Top Row: Red Team (5 Cards: TOP -> JGL -> MID -> ADC -> SUP) ----------------
        self.red_cards_row = QHBoxLayout()
        self.red_cards_row.setSpacing(8)
        self.container_layout.addLayout(self.red_cards_row)

        # ---------------- 3. Bottom Row: Blue Team (5 Cards: TOP -> JGL -> MID -> ADC -> SUP) ----------------
        self.blue_cards_row = QHBoxLayout()
        self.blue_cards_row.setSpacing(8)
        self.container_layout.addLayout(self.blue_cards_row)

        outer_layout.addWidget(self.main_container)
        self.set_window_opacity(self.cfg.opacity)

        # Initial state: clean waiting state (no fake players)
        self.show_waiting_state()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(max(10, x), max(10, y))

    def set_window_opacity(self, opacity: float):
        self.setWindowOpacity(max(0.3, min(1.0, opacity)))

    def _on_update_available(self, release_info: ReleaseInfo):
        self._pending_release = release_info
        self.banner_text.setText(f"🚀 Update Available: Glaive {release_info.tag_name} on GitHub")
        self.update_banner.show()
        print(f"[AutoUpdater] Update available: {release_info.tag_name}. Banner displayed.")

    def _trigger_update_download(self):
        if not self._pending_release:
            return
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Downloading...")

        def run_update():
            success = self.updater.apply_update_windows(self._pending_release.download_url)
            if not success:
                self.update_btn.setText("Failed")
                self.update_btn.setEnabled(True)

        t = threading.Thread(target=run_update, daemon=True)
        t.start()

    def show_waiting_state(self):
        """Clears all cards and displays the clean waiting placeholder."""
        self._clear_layout(self.red_cards_row)
        self._clear_layout(self.blue_cards_row)
        if hasattr(self, "waiting_container"):
            self.waiting_container.show()

    def display_players(self, players: List[PlayerScoutingData]):
        """
        Populates the 10 real player cards from active live match:
        - Top Row: Red Team (Team 200 / Chaos / Map Top), sorted TOP -> JGL -> MID -> ADC -> SUP
        - Bottom Row: Blue Team (Team 100 / Order / Map Bottom), sorted TOP -> JGL -> MID -> ADC -> SUP
        """
        if not players:
            self.show_waiting_state()
            return

        if hasattr(self, "waiting_container"):
            self.waiting_container.hide()

        self._clear_layout(self.red_cards_row)
        self._clear_layout(self.blue_cards_row)

        red_players = [p for p in players if p.team_id == 200]
        blue_players = [p for p in players if p.team_id == 100]

        if not red_players and not blue_players:
            # Fallback if team_ids not provided: first 5 top, second 5 bottom
            red_players = players[5:] if len(players) >= 10 else players[:len(players)//2]
            blue_players = players[:5] if len(players) >= 10 else players[len(players)//2:]
        elif not red_players:
            red_players = [p for p in players if p not in blue_players]
        elif not blue_players:
            blue_players = [p for p in players if p not in red_players]

        sorted_red = sort_players_by_role(red_players)
        sorted_blue = sort_players_by_role(blue_players)

        # Top Row (Red Side)
        for p in sorted_red:
            card = PlayerCardWidget(p)
            self.red_cards_row.addWidget(card)

        # Bottom Row (Blue Side)
        for p in sorted_blue:
            card = PlayerCardWidget(p)
            self.blue_cards_row.addWidget(card)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_status(self, status: str, match_title: str = ""):
        self._current_status = status
        self.setWindowTitle(f"Glaive - {status}")

    def toggle_overlay(self):
        if self.isVisible():
            self.hide()
            self._is_visible = False
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.apply_win32_optimizations()
            if sys.platform == "win32":
                try:
                    hwnd = int(self.winId())
                    HWND_TOPMOST = -1
                    SWP_NOMOVE = 0x0002
                    SWP_NOSIZE = 0x0001
                    SWP_SHOWWINDOW = 0x0040
                    ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                except Exception:
                    pass
            self._is_visible = True

    def open_settings(self):
        dlg = SettingsDialog(self.config_manager, parent=None)
        if dlg.exec():
            self.cfg = self.config_manager.config
            self.set_window_opacity(self.cfg.opacity)
            if self.cfg.mock_mode:
                from src.mock_data import get_mock_match_data
                self.display_players(get_mock_match_data())

        self.show()
        self.raise_()
        self.apply_win32_optimizations()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
