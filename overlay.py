"""Snipping Tool & Circle to Search selection overlay.

High-Performance, Zero-Lag Architecture:
1. Pre-renders dimmed background once at launch (zero stutter during dragging).
2. Per-monitor top control bar (centered on the active monitor, never split across bezels).
3. ⭕ Circle / Lasso: Ultra-smooth neon glow stroke, clean bounding calculation, no polygon flicker.
4. ◻️ Rectangle: Precision snip with Google Lens corner brackets and live dimension badge.
5. 🖥️ Full Screen: 1-click full snip.
6. Multi-monitor & High-DPI 100% pixel-perfect scaling.
7. Keyboard shortcuts: [1] Circle, [2] Rectangle, [3] Fullscreen, [Esc] Close.
"""
from enum import Enum
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPixmap, QCursor, QFont, QPainterPath, QGuiApplication
)
from PySide6.QtWidgets import QWidget

GOOGLE_BLUE = QColor(26, 115, 232)             # #1A73E8
GOOGLE_BLUE_GLOW = QColor(66, 133, 244, 90)     # #4285F4 with alpha
GOOGLE_CYAN_GLOW = QColor(0, 210, 255, 160)
GOOGLE_CORNER = QColor(255, 255, 255)
DIM_COLOR = QColor(15, 23, 42, 135)             # Slate dimming overlay


class SnipMode(Enum):
    CIRCLE = "circle"       # Freehand circle / lasso drawing
    RECTANGLE = "rect"     # Precision rectangular snip
    FULLSCREEN = "full"    # Fullscreen capture


class SelectionOverlay(QWidget):
    # Emits: (QPixmap of the cropped selection, QRect in absolute virtual-desktop coords)
    selection_made = Signal(QPixmap, QRect)
    cancelled = Signal()

    def __init__(self, bg_pixmap: QPixmap, vgeo: QRect, default_mode: SnipMode = SnipMode.CIRCLE):
        super().__init__()
        self._bg = bg_pixmap
        self._vgeo = vgeo

        # Pre-render dimmed background once for zero-lag 144Hz/60Hz rendering
        self._dimmed_bg = QPixmap(self._bg.size())
        self._dimmed_bg.setDevicePixelRatio(self._bg.devicePixelRatio())
        self._dimmed_bg.fill(Qt.transparent)
        p_dim = QPainter(self._dimmed_bg)
        p_dim.drawPixmap(0, 0, self._bg)
        p_dim.fillRect(self._dimmed_bg.rect(), DIM_COLOR)
        p_dim.end()

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)

        # Cover entire virtual desktop
        self.setGeometry(vgeo)

        self._mode = default_mode
        self._dragging = False
        self._start = QPoint()
        self._current = QPoint()
        self._points: list[QPoint] = []
        self._has_selection = False

        # Top bar buttons hitboxes
        self._btn_circle_rect = QRect()
        self._btn_rect_rect = QRect()
        self._btn_full_rect = QRect()
        self._btn_close_rect = QRect()
        self._hovered_btn = None
        self._last_active_screen_rect = QRect()

    def showFullScreenAllMonitors(self):
        self.show()
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.ActiveWindowFocusReason)

    # ---- active monitor helper ---------------------------------------
    def _get_active_monitor_rect(self) -> QRect:
        """Finds the local coordinate rectangle of the monitor under mouse cursor."""
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if not screen:
            return self.rect()

        sgeo = screen.geometry()
        lx = sgeo.x() - self._vgeo.x()
        ly = sgeo.y() - self._vgeo.y()
        return QRect(lx, ly, sgeo.width(), sgeo.height())

    # ---- painting -------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)

        # 1. Draw pre-rendered dimmed background (ultra-fast, zero redraw lag)
        p.drawPixmap(0, 0, self._dimmed_bg)

        # 2. Active selection cutout and stroke rendering
        if self._has_selection:
            p.setRenderHint(QPainter.Antialiasing, True)
            if self._mode == SnipMode.CIRCLE and len(self._points) > 1:
                self._draw_circle_selection(p)
            else:
                self._draw_rect_selection(p)

        # 3. Top control bar + bottom hint centered on active screen
        p.setRenderHint(QPainter.Antialiasing, True)
        active_screen = self._get_active_monitor_rect()
        self._draw_snipping_bar(p, active_screen)
        if not self._dragging:
            self._draw_bottom_hint(p, active_screen)

        p.end()

    def _draw_rect_selection(self, p: QPainter):
        rect = self._current_rect()
        if not rect.isValid() or rect.isEmpty() or rect.width() < 2 or rect.height() < 2:
            return

        # Punch out original crisp bright pixels
        p.drawPixmap(rect, self._bg, rect)

        # Glowing accent border
        glow_pen = QPen(GOOGLE_BLUE_GLOW, 5)
        p.setPen(glow_pen)
        p.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 3, 3)

        # Primary crisp Google Blue border
        main_pen = QPen(GOOGLE_BLUE, 2.5)
        p.setPen(main_pen)
        p.drawRoundedRect(rect, 3, 3)

        # Google Lens corner brackets
        self._draw_lens_corners(p, rect)

        # Live dimension badge while dragging
        if self._dragging:
            self._draw_dimension_badge(p, rect)

    def _draw_circle_selection(self, p: QPainter):
        if len(self._points) < 2:
            return

        # Build smooth path from freehand points
        path = QPainterPath()
        path.moveTo(self._points[0])
        for pt in self._points[1:]:
            path.lineTo(pt)

        # Glowing halo stroke (Google Cyan to Blue neon glow)
        halo_pen = QPen(GOOGLE_CYAN_GLOW, 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(halo_pen)
        p.drawPath(path)

        # Google Blue vibrant core stroke
        core_pen = QPen(GOOGLE_BLUE, 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(core_pen)
        p.drawPath(path)

        # White glowing tip at current cursor position
        current_pt = self._points[-1]
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(GOOGLE_BLUE, 2))
        p.drawEllipse(current_pt, 4, 4)

    def _draw_lens_corners(self, p: QPainter, rect: QRect):
        corner_len = min(16, max(6, min(rect.width(), rect.height()) // 4))
        p.setPen(QPen(GOOGLE_CORNER, 3.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))

        x1, y1 = rect.left(), rect.top()
        x2, y2 = rect.right(), rect.bottom()

        p.drawLine(x1, y1 + corner_len, x1, y1)
        p.drawLine(x1, y1, x1 + corner_len, y1)

        p.drawLine(x2 - corner_len, y1, x2, y1)
        p.drawLine(x2, y1, x2, y1 + corner_len)

        p.drawLine(x1, y2 - corner_len, x1, y2)
        p.drawLine(x1, y2, x1 + corner_len, y2)

        p.drawLine(x2 - corner_len, y2, x2, y2)
        p.drawLine(x2, y2 - corner_len, x2, y2)

    def _draw_dimension_badge(self, p: QPainter, rect: QRect):
        text = f"{rect.width()} × {rect.height()} px"
        font = QFont("Segoe UI", 9, QFont.Bold)
        p.setFont(font)

        badge_w, badge_h = 100, 24
        bx = rect.right() - badge_w
        by = rect.bottom() + 8
        if by + badge_h > self.rect().bottom():
            by = rect.top() - badge_h - 8
        if bx < 0:
            bx = rect.left()

        badge_rect = QRect(bx, by, badge_w, badge_h)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(32, 33, 36, 230))
        p.drawRoundedRect(badge_rect, 6, 6)

        p.setPen(QColor(255, 255, 255))
        p.drawText(badge_rect, Qt.AlignCenter, text)

    def _draw_snipping_bar(self, p: QPainter, active_screen: QRect):
        """Draws top control bar centered inside active screen."""
        bar_w = 480
        bar_h = 46
        cx = active_screen.center().x()
        bar_y = active_screen.top() + 20
        bar_rect = QRect(cx - bar_w // 2, bar_y, bar_w, bar_h)

        # Card shadow & dark glass background
        p.setPen(QPen(QColor(255, 255, 255, 45), 1))
        p.setBrush(QColor(28, 29, 32, 250))
        p.drawRoundedRect(bar_rect, 23, 23)

        # Google 4-color top accent line
        accent_h = 2.5
        accent_w = 120
        accent_x = cx - accent_w // 2
        p.fillRect(QRect(int(accent_x), bar_y, 30, int(accent_h)), QColor(66, 133, 244))   # Blue
        p.fillRect(QRect(int(accent_x + 30), bar_y, 30, int(accent_h)), QColor(234, 67, 53))   # Red
        p.fillRect(QRect(int(accent_x + 60), bar_y, 30, int(accent_h)), QColor(251, 188, 4))  # Yellow
        p.fillRect(QRect(int(accent_x + 90), bar_y, 30, int(accent_h)), QColor(52, 168, 83))   # Green

        font = QFont("Segoe UI", 10, QFont.DemiBold)
        p.setFont(font)

        btn_y = bar_rect.y() + 6
        btn_h = 34

        # 1. Circle / Freeform button
        self._btn_circle_rect = QRect(bar_rect.x() + 10, btn_y, 110, btn_h)
        self._render_bar_btn(
            p, self._btn_circle_rect, "⭕ Circle [1]",
            is_active=(self._mode == SnipMode.CIRCLE),
            is_hovered=(self._hovered_btn == "circle")
        )

        # 2. Rectangle button
        self._btn_rect_rect = QRect(bar_rect.x() + 126, btn_y, 115, btn_h)
        self._render_bar_btn(
            p, self._btn_rect_rect, "◻️ Rect [2]",
            is_active=(self._mode == SnipMode.RECTANGLE),
            is_hovered=(self._hovered_btn == "rect")
        )

        # 3. Fullscreen button
        self._btn_full_rect = QRect(bar_rect.x() + 247, btn_y, 120, btn_h)
        self._render_bar_btn(
            p, self._btn_full_rect, "🖥️ Full [3]",
            is_active=False,
            is_hovered=(self._hovered_btn == "full")
        )

        # 4. Close / Cancel button
        self._btn_close_rect = QRect(bar_rect.right() - 85, btn_y, 75, btn_h)
        self._render_bar_btn(
            p, self._btn_close_rect, "✕ Close",
            is_active=False,
            is_hovered=(self._hovered_btn == "close"),
            is_close=True
        )

    def _draw_bottom_hint(self, p: QPainter, active_screen: QRect):
        """Draws status pill centered inside active screen."""
        text = "Circle or drag around anything • Esc / Right-Click to close"
        font = QFont("Segoe UI", 10, QFont.Medium)
        p.setFont(font)

        badge_w, badge_h = 420, 32
        cx = active_screen.center().x()
        badge_y = active_screen.bottom() - 50
        badge_rect = QRect(cx - badge_w // 2, badge_y, badge_w, badge_h)

        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.setBrush(QColor(20, 21, 24, 225))
        p.drawRoundedRect(badge_rect, 16, 16)

        p.setPen(QColor(230, 233, 238))
        p.drawText(badge_rect, Qt.AlignCenter, text)

    def _render_bar_btn(self, p: QPainter, rect: QRect, text: str, is_active: bool, is_hovered: bool, is_close: bool = False):
        if is_active:
            p.setPen(Qt.NoPen)
            p.setBrush(GOOGLE_BLUE)
            p.drawRoundedRect(rect, 17, 17)
            p.setPen(QColor(255, 255, 255))
        elif is_hovered:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(234, 67, 53, 220) if is_close else QColor(255, 255, 255, 38))
            p.drawRoundedRect(rect, 17, 17)
            p.setPen(QColor(255, 255, 255))
        elif is_close:
            p.setPen(QPen(QColor(234, 67, 53, 100), 1))
            p.setBrush(QColor(234, 67, 53, 30))
            p.drawRoundedRect(rect, 17, 17)
            p.setPen(QColor(255, 120, 110))
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(Qt.NoBrush)
            p.setPen(QColor(218, 220, 224))

        p.drawText(rect, Qt.AlignCenter, text)

    # ---- helpers ----------------------------------------------------
    def _current_rect(self) -> QRect:
        return QRect(self._start, self._current).normalized()

    def _points_bounding_box(self) -> QRect:
        """Computes exact bounding box enclosing freehand points with gentle padding."""
        if not self._points:
            return QRect()
        min_x = min(pt.x() for pt in self._points)
        max_x = max(pt.x() for pt in self._points)
        min_y = min(pt.y() for pt in self._points)
        max_y = max(pt.y() for pt in self._points)
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        # Add 4px breathing room so looped strokes encompass edges nicely
        return QRect(min_x - 4, min_y - 4, w + 8, h + 8).normalized().intersected(self.rect())

    # ---- mouse interaction -------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()

        if event.button() == Qt.RightButton:
            self._cancel_and_close()
            return

        if event.button() == Qt.LeftButton:
            # Check top bar buttons first
            if self._btn_circle_rect.contains(pos):
                self._mode = SnipMode.CIRCLE
                self._has_selection = False
                self._points.clear()
                self.update()
                return

            if self._btn_rect_rect.contains(pos):
                self._mode = SnipMode.RECTANGLE
                self._has_selection = False
                self._points.clear()
                self.update()
                return

            if self._btn_full_rect.contains(pos):
                self._capture_fullscreen()
                return

            if self._btn_close_rect.contains(pos):
                self._cancel_and_close()
                return

            # Check if clicked inside bar bounding box
            active_screen = self._get_active_monitor_rect()
            cx = active_screen.center().x()
            bar_y = active_screen.top() + 20
            bar_box = QRect(cx - 245, bar_y, 490, 50)
            if bar_box.contains(pos):
                return

            # Start dragging / drawing
            self._dragging = True
            self._has_selection = True
            self._start = pos
            self._current = pos
            self._points = [pos]
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        # Update hovered button for top bar
        old_hover = self._hovered_btn
        if self._btn_circle_rect.contains(pos):
            self._hovered_btn = "circle"
        elif self._btn_rect_rect.contains(pos):
            self._hovered_btn = "rect"
        elif self._btn_full_rect.contains(pos):
            self._hovered_btn = "full"
        elif self._btn_close_rect.contains(pos):
            self._hovered_btn = "close"
        else:
            self._hovered_btn = None

        if old_hover != self._hovered_btn:
            self.update()

        if self._dragging:
            self._current = pos
            if self._mode == SnipMode.CIRCLE:
                if not self._points or (pos - self._points[-1]).manhattanLength() >= 2:
                    self._points.append(pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False

            if self._mode == SnipMode.CIRCLE and len(self._points) >= 4:
                rect = self._points_bounding_box()
            else:
                rect = self._current_rect()

            if rect.width() < 8 or rect.height() < 8:
                # Accidental micro-click, reset selection
                self._has_selection = False
                self._points.clear()
                self.update()
                return

            # Extract exact native pixel crop
            crop_pixmap = self._bg.copy(rect)

            # Absolute virtual coordinates for floating toolbar positioning
            abs_rect = QRect(
                rect.x() + self._vgeo.x(),
                rect.y() + self._vgeo.y(),
                rect.width(),
                rect.height(),
            )
            self.selection_made.emit(crop_pixmap, abs_rect)

    def _capture_fullscreen(self):
        active_screen = self._get_active_monitor_rect()
        crop_pixmap = self._bg.copy(active_screen)
        abs_rect = QRect(
            active_screen.x() + self._vgeo.x(),
            active_screen.y() + self._vgeo.y(),
            active_screen.width(),
            active_screen.height()
        )
        self.selection_made.emit(crop_pixmap, abs_rect)

    def _cancel_and_close(self):
        self.cancelled.emit()
        self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self._cancel_and_close()
        elif key in (Qt.Key_1, Qt.Key_C):
            self._mode = SnipMode.CIRCLE
            self.update()
        elif key in (Qt.Key_2, Qt.Key_R):
            self._mode = SnipMode.RECTANGLE
            self.update()
        elif key in (Qt.Key_3, Qt.Key_F):
            self._capture_fullscreen()
