"""Lightweight global hotkey using Win32 RegisterHotKey (no polling, no admin rights,
no interference with other shortcuts since it's a single registered combo)."""
import ctypes
import ctypes.wintypes as wt
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 1

# Win32 RegisterHotKey modifier constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class HotkeyListener:
    def __init__(self, mods: int, vk: int, callback, on_error=None):
        self.mods = mods
        self.vk = vk
        self.callback = callback
        self.on_error = on_error
        self._thread = None
        self._stop_flag = False
        self._thread_id = None
        self._ready_event = threading.Event()

    def start(self):
        self._stop_flag = False
        self._ready_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # Wait up to 500ms for registration to finish
        self._ready_event.wait(timeout=0.5)

    def _run(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        # Force message queue creation for this thread
        msg = wt.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)

        success = user32.RegisterHotKey(None, HOTKEY_ID, self.mods, self.vk)
        self._ready_event.set()

        if not success:
            err = kernel32.GetLastError()
            if self.on_error:
                try:
                    self.on_error(err)
                except Exception:
                    pass
            return

        try:
            while not self._stop_flag:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:  # WM_QUIT or error
                    break
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    try:
                        self.callback()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def update(self, mods: int, vk: int):
        """Re-register with a new combo safely."""
        self.stop()
        self.mods = mods
        self.vk = vk
        self.start()

    def stop(self):
        self._stop_flag = True
        if self._thread_id:
            # Post WM_QUIT to unblock GetMessageW
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.6)
        self._thread = None
        self._thread_id = None
