import ctypes
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
)

from config import MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT, DEFAULT_SETTINGS
import config as cfg


class HotkeyCaptureLabel(QLabel):
    """Click, then press a key combo; captures Windows virtual keys accurately."""

    def __init__(self):
        super().__init__("Click here, then press a key combo…")
        self.setStyleSheet(
            "QLabel {"
            "  background-color: #F8F9FA;"
            "  color: #3C4043;"
            "  border: 1.5px solid #DADCE0;"
            "  padding: 12px;"
            "  border-radius: 8px;"
            "  font-family: 'Segoe UI', Roboto, sans-serif;"
            "  font-size: 13px;"
            "  font-weight: 500;"
            "}"
            "QLabel:focus {"
            "  border: 2px solid #1A73E8;"
            "  background-color: #E8F0FE;"
            "  color: #1A73E8;"
            "}"
        )
        self.setFocusPolicy(Qt.StrongFocus)
        self.mods = 0
        self.vk = 0

    def set_combo(self, mods: int, vk: int, label: str):
        self.mods = mods
        self.vk = vk
        self.setText(label)

    def keyPressEvent(self, event):
        qt_mods = event.modifiers()
        mods = MOD_NOREPEAT
        parts = []
        if qt_mods & Qt.ControlModifier:
            mods |= MOD_CONTROL
            parts.append("Ctrl")
        if qt_mods & Qt.AltModifier:
            mods |= MOD_ALT
            parts.append("Alt")
        if qt_mods & Qt.ShiftModifier:
            mods |= MOD_SHIFT
            parts.append("Shift")
        if qt_mods & Qt.MetaModifier:
            mods |= MOD_WIN
            parts.append("Win")

        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return  # Modifier alone, wait for key

        if not parts:
            self.setText("Add at least one modifier (Ctrl/Alt/Shift/Win)")
            return

        # Use Windows native virtual key directly from Qt event
        native_vk = event.nativeVirtualKey()
        if native_vk > 0:
            vk = native_vk
        else:
            vk = key & 0xFF

        key_name = event.text().upper().strip()
        if not key_name or ord(key_name[0]) < 32:
            key_name = _get_key_display_name(key, vk)

        parts.append(key_name)
        self.mods = mods
        self.vk = vk
        self.setText("+".join(parts))


def _get_key_display_name(qt_key: int, vk: int) -> str:
    if Qt.Key_F1 <= qt_key <= Qt.Key_F24:
        return f"F{qt_key - Qt.Key_F1 + 1}"
    if 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    if Qt.Key_A <= qt_key <= Qt.Key_Z:
        return chr(qt_key)
    if Qt.Key_0 <= qt_key <= Qt.Key_9:
        return chr(qt_key)
    special_names = {
        Qt.Key_Space: "Space",
        Qt.Key_Return: "Enter",
        Qt.Key_Tab: "Tab",
        Qt.Key_Backspace: "Backspace",
        Qt.Key_Delete: "Delete",
        Qt.Key_Insert: "Insert",
        Qt.Key_Home: "Home",
        Qt.Key_End: "End",
        Qt.Key_PageUp: "PageUp",
        Qt.Key_PageDown: "PageDown",
        Qt.Key_Print: "PrintScreen",
        Qt.Key_Escape: "Esc",
    }
    return special_names.get(qt_key, f"Key_{vk:02X}")


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, on_apply):
        super().__init__()
        self.setWindowTitle("Circle to Search - Settings")
        self._settings = dict(settings)
        self._on_apply = on_apply
        self.setFixedWidth(420)

        self.setStyleSheet(
            """
            QDialog {
              background-color: #FAFAFA;
              font-family: 'Segoe UI Variable Display', 'Segoe UI', Roboto, sans-serif;
            }
            QLabel {
              color: #202124;
              font-size: 13px;
            }
            QCheckBox {
              color: #3C4043;
              font-size: 13px;
              spacing: 10px;
            }
            QCheckBox::indicator {
              width: 18px;
              height: 18px;
              border-radius: 5px;
              border: 2px solid #70757A;
              background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
              background-color: #1A73E8;
              border: 2px solid #1A73E8;
            }
            QPushButton#btn_save {
              background-color: #1A73E8;
              color: #FFFFFF;
              border: none;
              border-radius: 18px;
              padding: 10px 20px;
              font-size: 13px;
              font-weight: 600;
            }
            QPushButton#btn_save:hover {
              background-color: #1B66C9;
            }
            QPushButton#btn_secondary {
              background-color: #F1F3F4;
              color: #3C4043;
              border: 1px solid #DADCE0;
              border-radius: 18px;
              padding: 10px 16px;
              font-size: 13px;
              font-weight: 500;
            }
            QPushButton#btn_secondary:hover {
              background-color: #E8EAED;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        lbl_curr = QLabel(f"<b>Current shortcut:</b> <span style='color:#1A73E8;'>{self._settings.get('hotkey_label', 'Ctrl+Alt+C')}</span>")
        layout.addWidget(lbl_curr)

        lbl_new = QLabel("<b>Set new shortcut:</b>")
        layout.addWidget(lbl_new)

        self.capture = HotkeyCaptureLabel()
        layout.addWidget(self.capture)

        self.chk_autostart = QCheckBox("Start with Windows (System Tray)")
        self.chk_autostart.setChecked(self._settings.get("start_with_windows", False))
        layout.addWidget(self.chk_autostart)

        self.chk_keep = QCheckBox("Keep temporary screenshots (disabled by default)")
        self.chk_keep.setChecked(self._settings.get("keep_screenshots", False))
        layout.addWidget(self.chk_keep)

        row_buttons = QHBoxLayout()
        row_buttons.setSpacing(10)

        btn_default = QPushButton("Reset Default")
        btn_default.setObjectName("btn_secondary")
        btn_default.setCursor(Qt.PointingHandCursor)
        btn_default.clicked.connect(self._reset_default)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("btn_save")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._save)

        row_buttons.addWidget(btn_default)
        row_buttons.addStretch()
        row_buttons.addWidget(btn_cancel)
        row_buttons.addWidget(btn_save)
        layout.addLayout(row_buttons)

    def _reset_default(self):
        def_mods = DEFAULT_SETTINGS["hotkey_mods"]
        def_vk = DEFAULT_SETTINGS["hotkey_vk"]
        def_label = DEFAULT_SETTINGS["hotkey_label"]
        self.capture.set_combo(def_mods, def_vk, def_label)

    def _save(self):
        if self.capture.vk:
            self._settings["hotkey_mods"] = self.capture.mods
            self._settings["hotkey_vk"] = self.capture.vk
            self._settings["hotkey_label"] = self.capture.text()

        autostart = self.chk_autostart.isChecked()
        self._settings["start_with_windows"] = autostart
        cfg.set_autostart_enabled(autostart)

        self._settings["keep_screenshots"] = self.chk_keep.isChecked()
        cfg.save_settings(self._settings)
        self._on_apply(self._settings)
        self.accept()
