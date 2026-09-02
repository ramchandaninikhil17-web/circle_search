"""Lightweight global hotkey using Win32 RegisterHotKey (no polling, no admin rights,
no interference with other shortcuts since it's a single registered combo)."""
import ctypes
import ctypes.wintypes as wt
import threading

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312
HOTKEY_ID = 1

# Win32 RegisterHotKey modifier constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class HotkeyListener:
    def __init__(self, mods: int, vk: int, callback):
        self.mods = mods
        self.vk = vk
        self.callback = callback
        self._thread = None
        self._stop_flag = False
        self._thread_id = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, HOTKEY_ID, self.mods, self.vk):
            # Registration failed (likely conflict). Caller should surface this via tray notification.
            return
        msg = wt.MSG()
        try:
            while not self._stop_flag:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    try:
                        self.callback()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def update(self, mods: int, vk: int):
        """Re-register with a new combo (call from any thread)."""
        self.stop()
        self.mods = mods
        self.vk = vk
        self.start()

    def stop(self):
        self._stop_flag = True
        if self._thread_id:
            # WM_QUIT to unblock GetMessage
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        self._stop_flag = False
        self._thread_id = None
