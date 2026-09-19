import sys
import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Optional

# Win32 Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

KEY_MAP = {
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59,
    "z": 0x5A, "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33,
    "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38,
    "9": 0x39, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B, "space": 0x20,
    "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
}


class GlobalHotkeyListener(threading.Thread):
    """
    Ultra-reliable Global Hotkey Listener across all applications and DirectX games in Windows.
    Uses Win32 RegisterHotKey natively with zero polling CPU usage and fallback to pynput.
    """

    def __init__(self, hotkey_str: str, on_triggered: Callable[[], None]):
        super().__init__(daemon=True)
        self.raw_hotkey_str = hotkey_str
        self.on_triggered = on_triggered
        self._running = True
        self._thread_id: Optional[int] = None
        self._pynput_listener = None

    def _parse_win32_hotkey(self, hotkey_str: str):
        parts = [p.strip().lower() for p in hotkey_str.replace("-", "+").split("+")]
        mod = 0
        vk = 0
        for p in parts:
            if p in ["ctrl", "control"]:
                mod |= MOD_CONTROL
            elif p in ["alt"]:
                mod |= MOD_ALT
            elif p in ["shift"]:
                mod |= MOD_SHIFT
            elif p in ["win", "cmd", "super"]:
                mod |= MOD_WIN
            else:
                vk = KEY_MAP.get(p, ord(p.upper()) if len(p) == 1 else 0)
        return mod, vk

    def _run_win32(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        mod, vk = self._parse_win32_hotkey(self.raw_hotkey_str)

        if not vk:
            print(f"[HotkeyListener] Could not parse virtual key for: {self.raw_hotkey_str}")
            self._run_pynput_fallback()
            return

        HOTKEY_ID = 101
        res = user32.RegisterHotKey(None, HOTKEY_ID, mod | MOD_NOREPEAT, vk)
        if not res:
            # Fallback if already registered or failed
            print(f"[HotkeyListener] Win32 RegisterHotKey returned {res}, falling back to pynput...")
            self._run_pynput_fallback()
            return

        print(f"[HotkeyListener] Win32 Global Hotkey [{self.raw_hotkey_str.upper()}] successfully active.")
        msg = wintypes.MSG()
        while self._running:
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                try:
                    self.on_triggered()
                except Exception as e:
                    print(f"[HotkeyListener] Error in trigger callback: {e}")
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, HOTKEY_ID)

    def _run_pynput_fallback(self):
        try:
            from pynput import keyboard
            parts = [p.strip().lower() for p in self.raw_hotkey_str.replace("-", "+").split("+")]
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
            norm_str = "+".join(norm_parts)

            hotkey_map = {norm_str: self.on_triggered}
            with keyboard.GlobalHotKeys(hotkey_map) as listener:
                self._pynput_listener = listener
                listener.join()
        except Exception as e:
            print(f"[HotkeyListener] Fallback listener error: {e}")

    def run(self):
        if sys.platform == "win32":
            try:
                self._run_win32()
            except Exception as e:
                print(f"[HotkeyListener] Win32 error: {e}, using fallback.")
                self._run_pynput_fallback()
        else:
            self._run_pynput_fallback()

    def stop(self):
        self._running = False
        if sys.platform == "win32" and self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._pynput_listener:
            try:
                self._pynput_listener.stop()
            except Exception:
                pass

