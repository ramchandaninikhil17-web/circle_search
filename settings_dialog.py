from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox

from config import MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT
import config as cfg


class HotkeyCaptureLabel(QLabel):
    """Click, then press a key combo; captures Qt modifiers + key."""

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
            return  # modifier alone, wait for the real key

        if not parts:
            self.setText("Add at least one modifier (Ctrl/Alt/Shift/Win)")
            return

        vk = key & 0xFF if key < 0x01000000 else _qt_special_to_vk(key)
        parts.append(event.text().upper() or QT_KEY_NAMES.get(key, "?"))
        self.mods = mods
        self.vk = vk
        self.setText("+".join(parts))


QT_KEY_NAMES = {}


def _qt_special_to_vk(qt_key: int) -> int:
    if Qt.Key_F1 <= qt_key <= Qt.Key_F24:
        return 0x70 + (qt_key - Qt.Key_F1)
    return qt_key & 0xFF


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, on_apply):
        super().__init__()
        self.setWindowTitle("Circle to Search - Settings")
        self._settings = settings
        self._on_apply = on_apply
        self.setFixedWidth(380)

        self.setStyleSheet(
            "QDialog {"
            "  background-color: #FAFAFA;"
            "  font-family: 'Segoe UI Variable Display', 'Segoe UI', Roboto, sans-serif;"
            "}"
            "QLabel {"
            "  color: #202124;"
            "  font-size: 14px;"
            "}"
            "QCheckBox {"
            "  color: #3C4043;"
            "  font-size: 14px;"
            "  spacing: 12px;"
            "}"
            "QCheckBox::indicator {"
            "  width: 18px;"
            "  height: 18px;"
            "  border-radius: 6px;"
            "  border: 2px solid #70757A;"
            "  background-color: #FFFFFF;"
            "}"
            "QCheckBox::indicator:checked {"
            "  background-color: #1A73E8;"
            "  border: 2px solid #1A73E8;"
            "}"
            "QPushButton {"
            "  background-color: #1A73E8;"
            "  color: #FFFFFF;"
            "  border: none;"
            "  border-radius: 20px;"
            "  padding: 12px 24px;"
            "  font-size: 14px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "  background-color: #1B66C9;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #174EA6;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl_curr = QLabel(f"<b>Current shortcut:</b> <span style='color:#1A73E8;'>{settings.get('hotkey_label', '?')}</span>")
        layout.addWidget(lbl_curr)

        lbl_new = QLabel("<b>Set new shortcut:</b>")
        layout.addWidget(lbl_new)

        self.capture = HotkeyCaptureLabel()
        layout.addWidget(self.capture)

        self.chk_keep = QCheckBox("Keep screenshots (off by default - nothing saved)")
        self.chk_keep.setChecked(settings.get("keep_screenshots", False))
        layout.addWidget(self.chk_keep)

        btn_save = QPushButton("Save Settings")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

    def _save(self):
        if self.capture.vk:
            self._settings["hotkey_mods"] = self.capture.mods
            self._settings["hotkey_vk"] = self.capture.vk
            self._settings["hotkey_label"] = self.capture.text()
        self._settings["keep_screenshots"] = self.chk_keep.isChecked()
        cfg.save_settings(self._settings)
        self._on_apply(self._settings)
        self.accept()
