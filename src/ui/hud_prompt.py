import sys
import ctypes
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008


class HUDPromptWidget(QWidget):
    """
    Sleek, non-intrusive Top-Center HUD Notification Banner.
    Appears at the top-center of the screen during League of Legends loading screen
    notifying the player that live scouting data is ready and they can press [Ctrl + X].
    
    Guarantees:
    - 100% non-activating (WS_EX_NOACTIVATE): Never steals keyboard/mouse focus from League.
    - Smooth top-center positioning and auto-dismiss.
    - Clickable to toggle overlay immediately.
    """

    prompt_clicked = pyqtSignal()
    show_prompt_signal = pyqtSignal(int)
    hide_prompt_signal = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl+x", parent=None):
        super().__init__(parent)
        self.hotkey = hotkey.upper()
        self._auto_dismiss_timer = QTimer(self)
        self._auto_dismiss_timer.setSingleShot(True)
        self._auto_dismiss_timer.timeout.connect(self.hide_prompt)

        # Thread-safe slots
        self.show_prompt_signal.connect(self.show_prompt)
        self.hide_prompt_signal.connect(self.hide_prompt)

        # Window Flags: Frameless, Always on Top, Non-activating tool window
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.init_ui()
        self.apply_win32_optimizations()

    def apply_win32_optimizations(self):
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                new_style = current_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                # Force HWND_TOPMOST Z-order without stealing focus
                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            except Exception as e:
                print(f"[HUDPrompt] Error setting Win32 flags: {e}")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Pill Container
        self.container = QFrame()
        self.container.setObjectName("HUDPromptContainer")
        self.container.setStyleSheet("""
            QFrame#HUDPromptContainer {
                background-color: #000000;
                border: 1px solid #38bdf8;
                border-radius: 20px;
            }
            QFrame#HUDPromptContainer:hover {
                background-color: #0d1117;
                border: 1px solid #60a5fa;
            }
        """)
        self.container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        pill_layout = QHBoxLayout(self.container)
        pill_layout.setContentsMargins(16, 8, 14, 8)
        pill_layout.setSpacing(12)

        # Live Indicator / Icon
        icon_label = QLabel("⚔️")
        icon_label.setStyleSheet("font-size: 14px;")
        pill_layout.addWidget(icon_label)

        # Main Notification Text
        self.text_label = QLabel()
        self.update_hotkey_text(self.hotkey)
        pill_layout.addWidget(self.text_label)

        # Dismiss Button (✕)
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 4px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        dismiss_btn.clicked.connect(self.hide_prompt)
        pill_layout.addWidget(dismiss_btn)

        main_layout.addWidget(self.container)
        self.adjustSize()

    def update_hotkey_text(self, hotkey: str):
        self.hotkey = hotkey.upper()
        self.text_label.setText(
            f"<span style='color: #f8fafc; font-size: 12px; font-weight: 700;'>Live Match Detected</span> "
            f"<span style='color: #64748b;'>•</span> "
            f"<span style='color: #94a3b8; font-size: 11px;'>Press </span>"
            f"<span style='color: #38bdf8; font-size: 11px; font-weight: 800; background: rgba(56, 189, 248, 0.18); border: 1px solid rgba(56, 189, 248, 0.4); padding: 2px 7px; border-radius: 3px;'>{self.hotkey}</span> "
            f"<span style='color: #94a3b8; font-size: 11px;'>to toggle scouting</span>"
        )
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.adjustSize()

    def show_prompt(self, duration_ms: int = 10000):
        """Displays the prompt at the top-center of the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            w = self.sizeHint().width()
            h = self.sizeHint().height()
            x = geo.x() + (geo.width() - w) // 2
            y = geo.y() + 20
            self.setGeometry(x, y, w, h)

        self.show()
        self.raise_()
        self.apply_win32_optimizations()

        if duration_ms > 0:
            self._auto_dismiss_timer.start(duration_ms)

    def hide_prompt(self):
        self._auto_dismiss_timer.stop()
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.prompt_clicked.emit()
            self.hide_prompt()
        super().mousePressEvent(event)
