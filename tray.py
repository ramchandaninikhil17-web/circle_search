import os
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _make_vector_icon() -> QIcon:
    size = 64
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    rect = QRectF(6, 6, 52, 52)
    pen_w = 7.0

    # Google 4 colors
    colors = [
        QColor(234, 67, 53),   # Red (top-left)
        QColor(251, 188, 4),   # Yellow (bottom-left)
        QColor(52, 168, 83),   # Green (bottom-right)
        QColor(66, 133, 244),  # Blue (top-right)
    ]

    angles = [45 * 16, 135 * 16, 225 * 16, 315 * 16]
    span = 84 * 16

    for c, start_angle in zip(colors, angles):
        p.setPen(QPen(c, pen_w, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, start_angle, span)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(66, 133, 244))
    p.drawEllipse(QRectF(24, 24, 16, 16))

    p.end()
    return QIcon(pix)


def get_app_icon() -> QIcon:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(project_dir, "app_icon.ico")
    if os.path.isfile(ico_path):
        icon = QIcon(ico_path)
        if not icon.isNull():
            return icon
    return _make_vector_icon()


class TrayApp:
    def __init__(self, on_capture, on_settings, on_quit):
        self._on_capture = on_capture
        self.tray = QSystemTrayIcon(get_app_icon())
        self.tray.setToolTip("Circle to Search - Google Lens")

        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
              background-color: #FFFFFF;
              border: 1px solid #DADCE0;
              border-radius: 8px;
              padding: 6px;
              font-family: 'Segoe UI', Roboto, sans-serif;
              font-size: 13px;
            }
            QMenu::item {
              color: #202124;
              padding: 8px 20px;
              border-radius: 4px;
            }
            QMenu::item:selected {
              background-color: #E8F0FE;
              color: #1A73E8;
            }
            QMenu::separator {
              height: 1px;
              background-color: #E8EAED;
              margin: 4px 8px;
            }
            """
        )

        act_capture = QAction("🔍 Capture now", menu)
        act_capture.triggered.connect(on_capture)
        act_settings = QAction("⚙ Settings…", menu)
        act_settings.triggered.connect(on_settings)
        act_quit = QAction("✕ Exit", menu)
        act_quit.triggered.connect(on_quit)

        menu.addAction(act_capture)
        menu.addAction(act_settings)
        menu.addSeparator()
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def notify(self, title: str, message: str, is_warning: bool = False):
        icon = QSystemTrayIcon.Warning if is_warning else QSystemTrayIcon.Information
        self.tray.showMessage(title, message, icon, 4000)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._on_capture()
