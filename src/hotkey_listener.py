import threading
from typing import Callable, Optional
from pynput import keyboard

class GlobalHotkeyListener(threading.Thread):
    """
    Global low-latency hotkey listener across all applications in Windows.
    Toggles the Glaive overlay when user hits Ctrl + X (or custom hotkey).
    """

    def __init__(self, hotkey_str: str, on_triggered: Callable[[], None]):
        super().__init__(daemon=True)
        self.hotkey_str = self._normalize_hotkey(hotkey_str)
        self.on_triggered = on_triggered
        self._listener: Optional[keyboard.GlobalHotKeys] = None

    def _normalize_hotkey(self, hotkey_str: str) -> str:
        parts = [p.strip().lower() for p in hotkey_str.replace("-", "+").split("+")]
        norm_parts = []
        for p in parts:
            if p in ["ctrl", "control"]:
                norm_parts.append("<ctrl>")
            elif p in ["alt"]:
                norm_parts.append("<alt>")
            elif p in ["shift"]:
                norm_parts.append("<shift>")
            elif p in ["cmd", "win", "super"]:
                norm_parts.append("<cmd>")
            else:
                norm_parts.append(p)
        return "+".join(norm_parts)

    def run(self):
        try:
            hotkey_map = {
                self.hotkey_str: self.on_triggered
            }
            with keyboard.GlobalHotKeys(hotkey_map) as listener:
                self._listener = listener
                listener.join()
        except Exception as e:
            print(f"[HotkeyListener] Error starting global hotkey listener: {e}")

    def stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
