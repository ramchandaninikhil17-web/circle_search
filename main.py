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
from overlay import SelectionOverlay
from toolbar import ActionToolbar
from tray import TrayApp
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

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            self.qapp.setWindowIcon(QIcon(icon_path))

        self.bridge = Bridge()
        self.bridge.trigger.connect(self._on_activate)

        self._busy = False  # ignore rapid re-trigger while an overlay is open
        self._overlay = None
        self._toolbar = None

        # Setup single instance local server
        self.local_server = QLocalServer(self.qapp)
        QLocalServer.removeServer(SINGLE_INSTANCE_SOCKET)
        self.local_server.listen(SINGLE_INSTANCE_SOCKET)
        self.local_server.newConnection.connect(self._on_ipc_connection)

        self.hotkey = HotkeyListener(
            self.settings["hotkey_mods"], self.settings["hotkey_vk"],
            callback=lambda: self.bridge.trigger.emit(),
        )
        self.hotkey.start()

        self.tray = TrayApp(
            on_capture=lambda: self.bridge.trigger.emit(),
            on_settings=self._open_settings,
            on_quit=self._quit,
        )

        if trigger_on_start:
            # Trigger capture overlay after Qt event loop initializes
            QTimer.singleShot(100, lambda: self.bridge.trigger.emit())

    def _on_ipc_connection(self):
        socket = self.local_server.nextPendingConnection()
        if socket:
            socket.readyRead.connect(lambda: self._handle_ipc_message(socket))

    def _handle_ipc_message(self, socket):
        data = socket.readAll().data().decode("utf-8", errors="ignore")
        if "trigger" in data:
            self.bridge.trigger.emit()
        socket.disconnectFromServer()

    # ---- activation flow -------------------------------------------------
    def _on_activate(self):
        if self._busy:
            return
        self._busy = True
        try:
            bg_pixmap, vgeo = grab_virtual_desktop_qt()
        except Exception:
            self._busy = False
            return

        self._overlay = SelectionOverlay(bg_pixmap, vgeo)
        self._overlay.selection_made.connect(self._on_selection)
        self._overlay.cancelled.connect(self._on_overlay_closed)
        self._overlay.destroyed.connect(lambda: self._on_overlay_closed())
        self._overlay.showFullScreenAllMonitors()

    def _on_selection(self, crop_pixmap, abs_rect):
        if self._overlay:
            self._overlay.close()
            self._overlay = None

        self._toolbar = ActionToolbar(
            crop_pixmap, abs_rect,
            min_chars_for_text=self.settings.get("ocr_min_chars_for_text_suggestion", 2),
        )
        self._toolbar.closed.connect(self._on_overlay_closed)
        self._toolbar.show()

    def _on_overlay_closed(self):
        self._busy = False

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self._apply_new_hotkey)
        dlg.exec()

    def _apply_new_hotkey(self, settings: dict):
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
    """If another instance of Circle to Search is already running in background,
    notify it to trigger screen capture and return True."""
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_SOCKET)
    if socket.waitForConnected(200):
        socket.write(b"trigger\n")
        socket.waitForBytesWritten(200)
        socket.disconnectFromServer()
        return True
    return False


if __name__ == "__main__":
    trigger_flag = ("--trigger" in sys.argv) or len(sys.argv) == 1

    # Check if already running in background tray
    if try_trigger_existing_instance():
        sys.exit(0)

    # First instance startup
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)

    app = App(qapp, trigger_on_start=trigger_flag)
    sys.exit(app.run())
