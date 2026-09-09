"""Circle to Search for Windows - entry point.

Flow: Hotkey / Shortcut / Tray -> screen capture -> selection overlay -> action toolbar
      -> Google Lens search / local OCR / Copy.

Supports Single-Instance IPC: Double-clicking the Desktop shortcut will instantly
trigger screen capture on the already-running background instance with zero lag.
"""
import os
import sys
import ctypes

# Set explicit Windows Application User Model ID for crisp taskbar & notification grouping
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("google.circlesearch.windows.1.0")
except Exception:
    pass

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket

import config as cfg
from capture import grab_virtual_desktop_qt
from hotkey import HotkeyListener
from overlay import SelectionOverlay, SnipMode
from toolbar import ActionToolbar
from tray import TrayApp, get_app_icon
from settings_dialog import SettingsDialog

SINGLE_INSTANCE_SOCKET = "CircleToSearch_Windows_App_IPC"


class Bridge(QObject):
    """Hotkey fires on a raw Win32 thread; forward it to the Qt main thread
    via a signal so all UI work happens safely on the GUI thread."""
    trigger = Signal()


class App:
    def __init__(self, qapp: QApplication, trigger_on_start: bool = False):
        self.qapp = qapp
        self.settings = cfg.load_settings()

        self.qapp.setWindowIcon(get_app_icon())

        self.bridge = Bridge()
        self.bridge.trigger.connect(self._on_activate)

        self._busy = False
        self._overlay = None
        self._toolbar = None

        # Setup single instance local server
        self.local_server = QLocalServer(self.qapp)
        QLocalServer.removeServer(SINGLE_INSTANCE_SOCKET)
        self.local_server.listen(SINGLE_INSTANCE_SOCKET)
        self.local_server.newConnection.connect(self._on_ipc_connection)

        self.hotkey = HotkeyListener(
            self.settings["hotkey_mods"],
            self.settings["hotkey_vk"],
            callback=lambda: self.bridge.trigger.emit(),
            on_error=self._on_hotkey_error,
        )
        self.hotkey.start()

        self.tray = TrayApp(
            on_capture=lambda: self.bridge.trigger.emit(),
            on_settings=self._open_settings,
            on_quit=self._quit,
        )

        if trigger_on_start:
            # Trigger capture overlay after Qt event loop initializes
            QTimer.singleShot(150, lambda: self.bridge.trigger.emit())

    def _on_hotkey_error(self, err_code: int):
        label = self.settings.get("hotkey_label", "shortcut")
        self.tray.notify(
            "Shortcut Conflict",
            f"Could not register '{label}'. Another application is using this shortcut. Please update it in Settings.",
            is_warning=True,
        )

    def _on_ipc_connection(self):
        socket = self.local_server.nextPendingConnection()
        if socket:
            socket.disconnected.connect(socket.deleteLater)
            socket.readyRead.connect(lambda: self._handle_ipc_message(socket))
            if socket.bytesAvailable():
                self._handle_ipc_message(socket)

    def _handle_ipc_message(self, socket):
        try:
            data = socket.readAll().data().decode("utf-8", errors="ignore")
            if "trigger" in data:
                self.bridge.trigger.emit()
            socket.disconnectFromServer()
        except Exception:
            pass

    # ---- activation flow -------------------------------------------------
    def _on_activate(self):
        # 1. Check if overlay is already active and visible
        if self._overlay is not None:
            try:
                if self._overlay.isVisible():
                    self._overlay.raise_()
                    self._overlay.activateWindow()
                    return
                else:
                    self._overlay.close()
            except Exception:
                pass
            self._overlay = None

        # 2. If toolbar is open, close it cleanly
        if self._toolbar is not None:
            try:
                self._toolbar.close()
            except Exception:
                pass
            self._toolbar = None

        self._busy = True
        try:
            bg_pixmap, vgeo = grab_virtual_desktop_qt()
        except Exception:
            self._busy = False
            return

        pref_mode = SnipMode.RECTANGLE if self.settings.get("preferred_mode") == "rect" else SnipMode.CIRCLE
        try:
            self._overlay = SelectionOverlay(bg_pixmap, vgeo, default_mode=pref_mode)
            self._overlay.selection_made.connect(self._on_selection)
            self._overlay.cancelled.connect(self._on_overlay_closed)
            self._overlay.destroyed.connect(self._on_overlay_closed)
            self._overlay.showFullScreenAllMonitors()
        except Exception:
            self._overlay = None
            self._busy = False

    def _on_selection(self, crop_pixmap, abs_rect):
        if self._overlay:
            try:
                self._overlay.selection_made.disconnect()
                self._overlay.cancelled.disconnect()
            except Exception:
                pass
            try:
                self._overlay.close()
            except Exception:
                pass
            self._overlay = None

        try:
            self._toolbar = ActionToolbar(
                crop_pixmap, abs_rect,
                min_chars_for_text=self.settings.get("ocr_min_chars_for_text_suggestion", 2),
            )
            self._toolbar.closed.connect(self._on_toolbar_closed)
            self._toolbar.destroyed.connect(self._on_toolbar_closed)
            self._toolbar.show()
        except Exception:
            self._toolbar = None
            self._busy = False

    def _on_overlay_closed(self):
        self._overlay = None
        if self._toolbar is None:
            self._busy = False

    def _on_toolbar_closed(self):
        self._toolbar = None
        self._busy = False

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self._apply_new_settings)
        dlg.exec()

    def _apply_new_settings(self, settings: dict):
        self.settings = settings
        self.hotkey.update(settings["hotkey_mods"], settings["hotkey_vk"])

    def _quit(self):
        self.hotkey.stop()
        if self.local_server:
            self.local_server.close()
            QLocalServer.removeServer(SINGLE_INSTANCE_SOCKET)
        self.qapp.quit()

    def run(self):
        return self.qapp.exec()


def try_trigger_existing_instance() -> bool:
    """If an instance is already running in background, tell it to trigger snip."""
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_SOCKET)
    if socket.waitForConnected(250):
        socket.write(b"trigger\n")
        socket.waitForBytesWritten(250)
        socket.disconnectFromServer()
        return True
    return False


if __name__ == "__main__":
    # Ensure QApplication is initialized before any Qt sockets or IPC
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)

    is_tray_mode = "--tray" in sys.argv or "--background" in sys.argv
    is_trigger_mode = "--trigger" in sys.argv

    # If already running in background, signal it to trigger and exit immediately
    if try_trigger_existing_instance():
        sys.exit(0)

    # First instance startup
    # If launched with --tray, start silent in tray without popping overlay
    trigger_on_start = False if is_tray_mode else (is_trigger_mode or len(sys.argv) == 1)

    app = App(qapp, trigger_on_start=trigger_on_start)
    sys.exit(app.run())
