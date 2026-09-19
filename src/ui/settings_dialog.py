import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSlider, QCheckBox, QPushButton, QFrame, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.config import ConfigManager, AVAILABLE_REGIONS
from src.updater import AutoUpdater, ReleaseInfo
from src.ui.theme import MAIN_STYLESHEET
from src import __version__


class SettingsDialog(QDialog):
    """Clean monochrome settings modal for Glaive configuration."""

    update_check_done_signal = pyqtSignal(object)
    download_progress_signal = pyqtSignal(int)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.cfg = config_manager.config
        self.updater = AutoUpdater()
        self.update_check_done_signal.connect(self._on_update_check_result)
        self.download_progress_signal.connect(self._on_download_progress)
        
        self.setWindowTitle("Glaive Settings")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("GLAIVE CONFIGURATION")
        title.setObjectName("AppTitle")
        title_row.addWidget(title)

        ver_badge = QLabel(f"v{__version__}")
        ver_badge.setStyleSheet(
            "color: #94a3b8; font-size: 11px; font-weight: 700; "
            "background: rgba(255, 255, 255, 0.08); border-radius: 0px; padding: 2px 6px;"
        )
        title_row.addWidget(ver_badge)
        title_row.addStretch()
        layout.addLayout(title_row)

        subtitle = QLabel("Configure API keys, platform region, and overlay behavior.")
        subtitle.setObjectName("StatusLabel")
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
        layout.addWidget(sep)

        # 1. Riot API Key
        key_label = QLabel("Riot Developer API Key (from developer.riotgames.com):")
        key_label.setObjectName("PlayerName")
        layout.addWidget(key_label)

        self.key_input = QLineEdit(self.cfg.riot_api_key)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        layout.addWidget(self.key_input)

        # 2. Region / Platform
        region_label = QLabel("Default Platform Region:")
        region_label.setObjectName("PlayerName")
        layout.addWidget(region_label)

        self.region_combo = QComboBox()
        current_idx = 0
        for i, (name, code) in enumerate(AVAILABLE_REGIONS):
            self.region_combo.addItem(name, code)
            if code.lower() == self.cfg.default_platform.lower():
                current_idx = i
        self.region_combo.setCurrentIndex(current_idx)
        layout.addWidget(self.region_combo)

        # 3. Hotkey
        hotkey_label = QLabel("Global Toggle Hotkey:")
        hotkey_label.setObjectName("PlayerName")
        layout.addWidget(hotkey_label)

        self.hotkey_input = QLineEdit(self.cfg.hotkey)
        self.hotkey_input.setPlaceholderText("ctrl+x")
        layout.addWidget(self.hotkey_input)

        # 4. Opacity Slider
        opacity_row = QHBoxLayout()
        op_label = QLabel("Overlay Opacity:")
        op_label.setObjectName("PlayerName")
        opacity_row.addWidget(op_label)

        self.op_val_label = QLabel(f"{int(self.cfg.opacity * 100)}%")
        self.op_val_label.setObjectName("StatValue")
        opacity_row.addWidget(self.op_val_label)
        layout.addLayout(opacity_row)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(40, 100)
        self.opacity_slider.setValue(int(self.cfg.opacity * 100))
        self.opacity_slider.valueChanged.connect(self._on_opacity_change)
        layout.addWidget(self.opacity_slider)

        # 5. Checkboxes
        self.mock_check = QCheckBox("Enable Mock / Preview Mode (Test 10-player data without active game)")
        self.mock_check.setChecked(self.cfg.mock_mode)
        layout.addWidget(self.mock_check)

        self.top_check = QCheckBox("Always on Top (Render above League of Legends)")
        self.top_check.setChecked(self.cfg.always_on_top)
        layout.addWidget(self.top_check)

        # 6. Auto-Updater Section
        update_frame = QFrame()
        update_frame.setStyleSheet(
            "background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); "
            "border-radius: 0px; padding: 6px;"
        )
        update_layout = QHBoxLayout(update_frame)
        update_layout.setContentsMargins(8, 6, 8, 6)

        self.update_status_lbl = QLabel("Updates: Up to date")
        self.update_status_lbl.setObjectName("StatusLabel")
        update_layout.addWidget(self.update_status_lbl)
        update_layout.addStretch()

        self.check_update_btn = QPushButton("Check for Updates")
        self.check_update_btn.clicked.connect(self._check_for_updates_async)
        update_layout.addWidget(self.check_update_btn)
        layout.addWidget(update_frame)

        layout.addSpacing(6)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.16); border: 1px solid rgba(255, 255, 255, 0.35); font-weight: 700;"
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_opacity_change(self, val: int):
        self.op_val_label.setText(f"{val}%")

    def _check_for_updates_async(self):
        self.check_update_btn.setEnabled(False)
        self.update_status_lbl.setText("Checking GitHub for updates...")

        def run_check():
            info = self.updater.check_for_updates()
            self.update_check_done_signal.emit(info)

        t = threading.Thread(target=run_check, daemon=True)
        t.start()

    def _on_update_check_result(self, release_info: ReleaseInfo | None):
        self.check_update_btn.setEnabled(True)
        if release_info:
            self.update_status_lbl.setText(f"New Version Found: {release_info.tag_name}")
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"A new version of Glaive ({release_info.tag_name}) is available on GitHub!\n\n"
                f"Release details:\n{release_info.release_notes[:200]}\n\n"
                f"Would you like to download and install this update?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._apply_update(release_info.download_url)
        else:
            self.update_status_lbl.setText(f"Glaive v{__version__} is up to date!")

    def _on_download_progress(self, percent: int):
        self.update_status_lbl.setText(f"Downloading update ({percent}%)...")

    def _apply_update(self, download_url: str):
        self.update_status_lbl.setText("Downloading update (0%)...")
        self.check_update_btn.setEnabled(False)

        def on_progress(pct: int):
            self.download_progress_signal.emit(pct)

        def run_apply():
            success = self.updater.apply_update_windows(download_url, progress_callback=on_progress)
            if not success:
                self.update_status_lbl.setText("Failed to download update.")
                self.check_update_btn.setEnabled(True)

        t = threading.Thread(target=run_apply, daemon=True)
        t.start()

    def _on_save(self):
        new_key = self.key_input.text().strip()
        new_platform = self.region_combo.currentData()
        new_hotkey = self.hotkey_input.text().strip().lower() or "ctrl+x"
        new_opacity = self.opacity_slider.value() / 100.0
        new_mock = self.mock_check.isChecked()
        new_top = self.top_check.isChecked()

        self.config_manager.update(
            riot_api_key=new_key,
            default_platform=new_platform,
            hotkey=new_hotkey,
            opacity=new_opacity,
            mock_mode=new_mock,
            always_on_top=new_top
        )
        self.accept()
