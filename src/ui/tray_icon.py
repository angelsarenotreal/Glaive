import os
from typing import Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from src.asset_manager import get_base_asset_dir
from src import __version__


class GlaiveTrayIcon(QSystemTrayIcon):
    """
    System Tray Icon for Glaive:
    - Lives in the Windows notification area / taskbar tray.
    - Left-click or double-click to toggle the overlay.
    - Right-click menu for quick actions (Toggle, Mock Lobby, Settings, Check Updates, Exit).
    """

    toggle_overlay_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    trigger_mock_requested = pyqtSignal()
    check_updates_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_icon()
        self.init_menu()
        self.setToolTip(f"Glaive v{__version__} · LoL In-Game Overlay")
        self.activated.connect(self._on_activated)

    def init_icon(self):
        icon_file = get_base_asset_dir() / "icon.png"
        if not icon_file.exists():
            icon_file = get_base_asset_dir() / "icon.ico"
        if icon_file.exists():
            self.setIcon(QIcon(str(icon_file)))

    def init_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #111722;
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QMenu::item:selected {
                background-color: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.1);
                margin: 4px 6px;
            }
        """)

        # Header Title
        title_action = QAction(f"⚔ GLAIVE v{__version__}", menu)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        # Toggle Overlay
        toggle_action = QAction("Toggle Overlay (Ctrl+X)", menu)
        toggle_action.triggered.connect(self.toggle_overlay_requested.emit)
        menu.addAction(toggle_action)

        # Preview Mock Data
        mock_action = QAction("Preview Lobby (Mock)", menu)
        mock_action.triggered.connect(self.trigger_mock_requested.emit)
        menu.addAction(mock_action)

        # Settings
        settings_action = QAction("⚙ Settings...", menu)
        settings_action.triggered.connect(self.open_settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Check Updates
        update_action = QAction("Check for Updates", menu)
        update_action.triggered.connect(self.check_updates_requested.emit)
        menu.addAction(update_action)

        menu.addSeparator()

        # Exit
        quit_action = QAction("Quit Glaive", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle_overlay_requested.emit()

    def notify(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        """Displays native Windows balloon/toast notification from the tray."""
        if self.isVisible():
            self.showMessage(title, message, icon, 4000)
