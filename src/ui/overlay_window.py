import os
import sys
import ctypes
import threading
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGraphicsOpacityEffect, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QMouseEvent, QColor, QIcon

from src.analytics import PlayerScoutingData
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


class GlaiveOverlayWindow(QWidget):
    """
    Ultra-lightweight, hardware-accelerated, transparent monochrome overlay window.
    Engineered for zero FPS impact, auto-updates, and no focus stealing.
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

        # Window Flags: Frameless, Always On Top, Tool Window
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Set Icon
        icon_path = os.path.abspath("assets/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        self.resize(1180, 680)
        self.center_on_screen()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        # Main Obsidian Container
        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")
        self.container_layout = QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(14, 12, 14, 14)
        self.container_layout.setSpacing(10)

        # ---------------- 0. Update Alert Banner (Hidden by default) ----------------
        self.update_banner = QFrame()
        self.update_banner.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.28); "
            "border-radius: 6px; padding: 4px 8px;"
        )
        self.update_banner.hide()
        banner_layout = QHBoxLayout(self.update_banner)
        banner_layout.setContentsMargins(6, 4, 6, 4)

        self.banner_text = QLabel("A new version of Glaive is available.")
        self.banner_text.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 700;")
        banner_layout.addWidget(self.banner_text)
        banner_layout.addStretch()

        self.update_btn = QPushButton("Update & Restart")
        self.update_btn.setStyleSheet(
            "background-color: #ffffff; color: #000000; font-weight: 800; padding: 3px 10px;"
        )
        self.update_btn.clicked.connect(self._trigger_update_download)
        banner_layout.addWidget(self.update_btn)

        dismiss_update_btn = QPushButton("✕")
        dismiss_update_btn.setObjectName("IconButton")
        dismiss_update_btn.clicked.connect(self.update_banner.hide)
        banner_layout.addWidget(dismiss_update_btn)

        self.container_layout.addWidget(self.update_banner)

        # ---------------- 1. Top Header Bar ----------------
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 6, 8, 8)

        # App Brand & Status
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_label = QLabel("GLAIVE")
        title_label.setObjectName("AppTitle")
        title_row.addWidget(title_label)

        ver_label = QLabel(f"v{__version__}")
        ver_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700;")
        title_row.addWidget(ver_label)
        title_row.addStretch()
        brand_layout.addLayout(title_row)

        self.status_label = QLabel("● WAITING FOR MATCH (PORT 2999)")
        self.status_label.setObjectName("StatusLabel")
        brand_layout.addWidget(self.status_label)
        header_layout.addLayout(brand_layout)

        header_layout.addStretch()

        # Center Match Queue Header
        self.match_title_label = QLabel("LIVE SCOUTING REPORT")
        self.match_title_label.setStyleSheet(
            "color: #ffffff; font-size: 13px; font-weight: 700; letter-spacing: 1.5px;"
        )
        header_layout.addWidget(self.match_title_label)

        header_layout.addStretch()

        # Right Action Controls
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        hotkey_hint = QLabel(f"[{self.cfg.hotkey.upper()}] Toggle")
        hotkey_hint.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600;")
        actions_layout.addWidget(hotkey_hint)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.open_settings)
        actions_layout.addWidget(settings_btn)

        hide_btn = QPushButton("✕")
        hide_btn.setObjectName("IconButton")
        hide_btn.clicked.connect(self.toggle_overlay)
        actions_layout.addWidget(hide_btn)

        header_layout.addLayout(actions_layout)
        self.container_layout.addWidget(header_frame)

        # ---------------- 2. Dual-Column Player Body ----------------
        self.columns_layout = QHBoxLayout()
        self.columns_layout.setSpacing(14)

        # --- Blue Team Column ---
        self.blue_column = QVBoxLayout()
        self.blue_column.setSpacing(8)

        blue_header = QFrame()
        blue_header.setStyleSheet("background: rgba(255, 255, 255, 0.04); border-radius: 6px; padding: 4px;")
        blue_h_layout = QHBoxLayout(blue_header)
        blue_h_layout.setContentsMargins(6, 2, 6, 2)
        blue_title = QLabel("ALLY TEAM (BLUE)")
        blue_title.setObjectName("TeamHeader")
        blue_title.setStyleSheet("color: #e2e8f0;")
        blue_h_layout.addWidget(blue_title)
        blue_h_layout.addStretch()
        self.blue_summary_label = QLabel("Avg Rank: --")
        self.blue_summary_label.setObjectName("TeamSubtext")
        blue_h_layout.addWidget(self.blue_summary_label)
        self.blue_column.addWidget(blue_header)

        self.blue_cards_layout = QVBoxLayout()
        self.blue_cards_layout.setSpacing(6)
        self.blue_column.addLayout(self.blue_cards_layout)
        self.blue_column.addStretch()

        # --- Red Team Column ---
        self.red_column = QVBoxLayout()
        self.red_column.setSpacing(8)

        red_header = QFrame()
        red_header.setStyleSheet("background: rgba(255, 255, 255, 0.04); border-radius: 6px; padding: 4px;")
        red_h_layout = QHBoxLayout(red_header)
        red_h_layout.setContentsMargins(6, 2, 6, 2)
        red_title = QLabel("ENEMY TEAM (RED)")
        red_title.setObjectName("TeamHeader")
        red_title.setStyleSheet("color: #f1f5f9;")
        red_h_layout.addWidget(red_title)
        red_h_layout.addStretch()
        self.red_summary_label = QLabel("Avg Rank: --")
        self.red_summary_label.setObjectName("TeamSubtext")
        red_h_layout.addWidget(self.red_summary_label)
        self.red_column.addWidget(red_header)

        self.red_cards_layout = QVBoxLayout()
        self.red_cards_layout.setSpacing(6)
        self.red_column.addLayout(self.red_cards_layout)
        self.red_column.addStretch()

        self.columns_layout.addLayout(self.blue_column, 1)
        self.columns_layout.addLayout(self.red_column, 1)
        self.container_layout.addLayout(self.columns_layout)

        outer_layout.addWidget(self.main_container)
        self.set_window_opacity(self.cfg.opacity)

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, max(y, 40))

    def set_window_opacity(self, opacity: float):
        self.setWindowOpacity(max(0.3, min(1.0, opacity)))

    def _on_update_available(self, release_info: ReleaseInfo):
        self._pending_release = release_info
        self.banner_text.setText(f"🚀 Update Available: Glaive {release_info.tag_name} on GitHub")
        self.update_banner.show()

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

    def display_players(self, players: List[PlayerScoutingData]):
        self._clear_layout(self.blue_cards_layout)
        self._clear_layout(self.red_cards_layout)

        blue_players = [p for p in players if p.team_id == 100]
        red_players = [p for p in players if p.team_id == 200]

        if not blue_players and not red_players:
            blue_players = players[:5]
            red_players = players[5:]

        for p in blue_players:
            card = PlayerCardWidget(p)
            self.blue_cards_layout.addWidget(card)

        for p in red_players:
            card = PlayerCardWidget(p)
            self.red_cards_layout.addWidget(card)

        self._update_team_summary(blue_players, self.blue_summary_label)
        self._update_team_summary(red_players, self.red_summary_label)

    def _update_team_summary(self, players: List[PlayerScoutingData], label: QLabel):
        if not players:
            label.setText("No Data")
            return
        total_wr = sum(p.ranked_winrate for p in players if p.ranked_wins + p.ranked_losses > 0)
        valid_wr_count = sum(1 for p in players if p.ranked_wins + p.ranked_losses > 0)
        avg_wr = total_wr / max(valid_wr_count, 1) if valid_wr_count > 0 else 0
        label.setText(f"Avg WR: {avg_wr:.0f}% · {len(players)} Players")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_status(self, status: str, match_title: str = ""):
        self.status_label.setText(status)
        if match_title:
            self.match_title_label.setText(match_title)

    def toggle_overlay(self):
        if self.isVisible():
            self.hide()
            self._is_visible = False
        else:
            self.show()
            self.apply_win32_optimizations()
            self._is_visible = True

    def open_settings(self):
        dlg = SettingsDialog(self.config_manager, self)
        if dlg.exec():
            self.cfg = self.config_manager.config
            self.set_window_opacity(self.cfg.opacity)
            if self.cfg.mock_mode:
                from src.mock_data import get_mock_match_data
                self.display_players(get_mock_match_data())
                self.set_status("● PREVIEW MODE (MOCK DATA)", "PREVIEW · DIAMOND I LOBBY")

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
