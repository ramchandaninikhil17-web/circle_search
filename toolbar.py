"""Floating action toolbar next to the selection.
Appears instantly with Google Lens search, local OCR text extraction,
instant clipboard copying, and quick save.
"""
from datetime import datetime
from PySide6.QtCore import Qt, QRect, QThread, Signal, QTimer
from PySide6.QtGui import QGuiApplication, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QTextEdit, QFrame, QApplication, QGraphicsDropShadowEffect,
    QFileDialog
)

import ocr as ocr_mod
import image_search
from capture import qpixmap_to_pil


class OcrWorker(QThread):
    done = Signal(str)

    def __init__(self, pil_image):
        super().__init__()
        self._img = pil_image

    def run(self):
        try:
            text = ocr_mod.recognize_text(self._img)
            self.done.emit(text)
        except Exception:
            self.done.emit("")


class SearchWorker(QThread):
    done = Signal(bool, str)

    def __init__(self, pil_image):
        super().__init__()
        self._img = pil_image

    def run(self):
        try:
            ok, msg = image_search.search_image(self._img)
            self.done.emit(ok, msg)
        except Exception as e:
            self.done.emit(False, str(e))


class ActionToolbar(QWidget):
    closed = Signal()

    def __init__(self, crop_pixmap: QPixmap, abs_rect: QRect, min_chars_for_text: int = 2):
        super().__init__()
        self._crop_pixmap = crop_pixmap
        self._crop_pil = qpixmap_to_pil(crop_pixmap)
        self._min_chars = min_chars_for_text
        self._detected_text = None
        self._search_thread = None
        self._ocr_thread = None
        self._abs_rect = abs_rect

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self._build_ui()
        self._position_near(abs_rect)

        # Background OCR worker for instantaneous UI response
        self.status.setText("🔍 Scanning text…")
        self._ocr_thread = OcrWorker(self._crop_pil)
        self._ocr_thread.done.connect(self._on_ocr_done)
        self._ocr_thread.finished.connect(self._ocr_thread.deleteLater)
        self._ocr_thread.start()

    # ---- UI ---------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QFrame(self)
        card.setObjectName("card")
        card.setStyleSheet(
            """
            #card {
              background-color: #FFFFFF;
              border-radius: 18px;
              border: 1px solid #E8EAED;
            }
            QPushButton {
              background-color: #F8F9FA;
              color: #3C4043;
              border: 1px solid #E8EAED;
              border-radius: 16px;
              padding: 8px 16px;
              font-family: 'Segoe UI Variable Display', 'Segoe UI', Roboto, sans-serif;
              font-size: 13px;
              font-weight: 600;
            }
            QPushButton:hover {
              background-color: #F1F3F4;
              border-color: #DADCE0;
            }
            QPushButton:pressed {
              background-color: #E8EAED;
            }
            QPushButton:disabled {
              background-color: #F1F3F4;
              color: #9AA0A6;
              border-color: #E8EAED;
            }
            QPushButton#btn_primary {
              background-color: #1A73E8;
              color: #FFFFFF;
              border: 1px solid #1A73E8;
            }
            QPushButton#btn_primary:hover {
              background-color: #1B66C9;
              border-color: #1B66C9;
            }
            QPushButton#btn_primary:pressed {
              background-color: #174EA6;
            }
            QPushButton#suggested {
              background-color: #E8F0FE;
              color: #1A73E8;
              border: 1.5px solid #1A73E8;
            }
            QPushButton#suggested:hover {
              background-color: #D2E3FC;
            }
            QPushButton#btn_close {
              background-color: #F8F9FA;
              color: #5F6368;
              font-weight: bold;
              border: 1px solid #E8EAED;
              border-radius: 16px;
            }
            QPushButton#btn_close:hover {
              background-color: #FCE8E6;
              color: #D93025;
              border-color: #F28B82;
            }
            QTextEdit {
              background-color: #F8F9FA;
              color: #202124;
              border: 1px solid #E8EAED;
              border-radius: 12px;
              padding: 10px;
              font-family: 'Segoe UI', Roboto, sans-serif;
              font-size: 13px;
            }
            QLabel#status {
              color: #1A73E8;
              font-family: 'Segoe UI Variable Display', 'Segoe UI', Roboto, sans-serif;
              font-size: 12px;
              font-weight: 600;
              padding: 0 4px;
            }
            #google_bar {
              background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4285F4, stop:0.25 #4285F4, stop:0.2501 #EA4335, stop:0.5 #EA4335, stop:0.5001 #FBBC04, stop:0.75 #FBBC04, stop:0.7501 #34A853, stop:1 #34A853);
              border-top-left-radius: 17px;
              border-top-right-radius: 17px;
              min-height: 4px;
              max-height: 4px;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(shadow)

        outer.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # Google 4-color accent strip
        google_bar = QFrame(card)
        google_bar.setObjectName("google_bar")
        inner.addWidget(google_bar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 10, 12, 12)
        content_layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(6)

        self.btn_image = QPushButton("🔍 Google Lens")
        self.btn_image.setObjectName("btn_primary")
        self.btn_image.setCursor(Qt.PointingHandCursor)

        self.btn_text = QPushButton("📝 Text")
        self.btn_text.setCursor(Qt.PointingHandCursor)

        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setCursor(Qt.PointingHandCursor)

        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setCursor(Qt.PointingHandCursor)

        self.btn_cancel = QPushButton("✕ Close")
        self.btn_cancel.setObjectName("btn_close")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setToolTip("Close (Esc)")

        for b in (self.btn_image, self.btn_text, self.btn_copy, self.btn_save, self.btn_cancel):
            row.addWidget(b)
        content_layout.addLayout(row)

        self.status = QLabel("")
        self.status.setObjectName("status")
        content_layout.addWidget(self.status)

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(False)
        self.text_preview.setVisible(False)
        self.text_preview.setFixedHeight(100)
        self.text_preview.setFixedWidth(380)
        content_layout.addWidget(self.text_preview)

        self.text_action_row = QHBoxLayout()
        self.btn_copy_text = QPushButton("📋 Copy Text")
        self.btn_copy_text.setCursor(Qt.PointingHandCursor)
        self.btn_copy_text.setVisible(False)
        self.btn_copy_text.clicked.connect(self._on_copy_text)

        self.btn_search_text = QPushButton("🔍 Search Google")
        self.btn_search_text.setObjectName("btn_primary")
        self.btn_search_text.setVisible(False)
        self.btn_search_text.setCursor(Qt.PointingHandCursor)
        self.btn_search_text.clicked.connect(self._on_search_text)

        self.text_action_row.addWidget(self.btn_copy_text)
        self.text_action_row.addWidget(self.btn_search_text)
        content_layout.addLayout(self.text_action_row)

        inner.addLayout(content_layout)

        self.btn_image.clicked.connect(self._on_image_search)
        self.btn_text.clicked.connect(self._on_text_toggle)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _position_near(self, abs_rect: QRect):
        screen = QGuiApplication.screenAt(abs_rect.center()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        self.adjustSize()
        w = max(420, self.width())
        h = max(95, self.height())
        x = min(abs_rect.right() + 12, avail.right() - w)
        y = abs_rect.top()
        if y + h > avail.bottom():
            y = max(avail.top(), avail.bottom() - h)
        if x < avail.left():
            x = avail.left()
        self.move(x, y)

    def _reclamp_to_screen(self):
        """Ensures toolbar never expands off-screen when toggling text."""
        self.adjustSize()
        geom = self.geometry()
        screen = QGuiApplication.screenAt(geom.center()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()

        new_x = geom.x()
        new_y = geom.y()

        if new_x + geom.width() > avail.right():
            new_x = avail.right() - geom.width()
        if new_x < avail.left():
            new_x = avail.left()

        if new_y + geom.height() > avail.bottom():
            new_y = avail.bottom() - geom.height()
        if new_y < avail.top():
            new_y = avail.top()

        self.move(new_x, new_y)

    # ---- OCR callback -------------------------------------------------
    def _on_ocr_done(self, text: str):
        self._detected_text = text.strip()
        if len(self._detected_text) >= self._min_chars:
            self.btn_text.setObjectName("suggested")
            self.btn_text.style().unpolish(self.btn_text)
            self.btn_text.style().polish(self.btn_text)
            words = len(self._detected_text.split())
            self.btn_text.setText(f"✨ Text ({words}w)")
            self.status.setStyleSheet("color: #188038; font-weight: 600;")
            preview_snippet = self._detected_text.replace("\n", " ").strip()
            if len(preview_snippet) > 40:
                self.status.setText(f'✓ Text: "{preview_snippet[:37]}…"')
            else:
                self.status.setText(f'✓ Text: "{preview_snippet}"')
        else:
            self.status.setStyleSheet("color: #5F6368; font-weight: 500;")
            self.status.setText("Visual selection ready")

    # ---- actions -------------------------------------------------
    def _on_image_search(self):
        clipboard = QApplication.clipboard()
        clipboard.setImage(self._crop_pixmap.toImage())

        self.btn_image.setEnabled(False)
        self.btn_image.setText("Searching…")
        self.status.setStyleSheet("color: #1A73E8; font-weight: 600;")
        self.status.setText("Opening Google Lens…")

        self._search_thread = SearchWorker(self._crop_pil)
        self._search_thread.done.connect(self._on_search_done)
        self._search_thread.finished.connect(self._search_thread.deleteLater)
        self._search_thread.start()

    def _on_search_done(self, ok: bool, message: str):
        if ok:
            self.status.setStyleSheet("color: #188038; font-weight: 600;")
            self.status.setText(f"✓ {message}")
            QTimer.singleShot(400, self.close)
        else:
            self.btn_image.setEnabled(True)
            self.btn_image.setText("🔍 Google Lens")
            self.status.setStyleSheet("color: #D93025; font-weight: 600;")
            self.status.setText(message)

    def _on_text_toggle(self):
        if self._detected_text is None:
            self.status.setText("Reading text…")
            return
        if not self._detected_text:
            self.status.setStyleSheet("color: #D93025; font-weight: 600;")
            self.status.setText("No text found in selection")
            return

        is_visible = self.text_preview.isVisible()
        if not is_visible:
            # Preserve user modifications if they already typed/edited in text preview
            if not self.text_preview.toPlainText().strip():
                self.text_preview.setPlainText(self._detected_text)
            self.text_preview.setVisible(True)
            self.btn_copy_text.setVisible(True)
            self.btn_search_text.setVisible(True)
        else:
            self.text_preview.setVisible(False)
            self.btn_copy_text.setVisible(False)
            self.btn_search_text.setVisible(False)
        self._reclamp_to_screen()

    def _on_search_text(self):
        text = self.text_preview.toPlainText() or self._detected_text
        if text:
            image_search.search_text_on_google(text)
        self.close()

    def _on_copy_text(self):
        text = self.text_preview.toPlainText() or self._detected_text
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.btn_copy_text.setEnabled(False)
            self.status.setStyleSheet("color: #188038; font-weight: 600;")
            self.status.setText("✓ Text copied to clipboard!")
            QTimer.singleShot(900, self.close)

    def _on_copy(self):
        clipboard = QApplication.clipboard()
        if self.text_preview.isVisible() and (self.text_preview.toPlainText() or self._detected_text):
            clipboard.setText(self.text_preview.toPlainText() or self._detected_text)
            self.btn_copy.setEnabled(False)
            self.status.setStyleSheet("color: #188038; font-weight: 600;")
            self.status.setText("✓ Text copied to clipboard!")
        else:
            clipboard.setImage(self._crop_pixmap.toImage())
            self.btn_copy.setEnabled(False)
            self.status.setStyleSheet("color: #188038; font-weight: 600;")
            self.status.setText("✓ Image copied to clipboard!")
        QTimer.singleShot(900, self.close)

    def _on_save(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Snip_{timestamp}.png"
        dialog = QFileDialog(self, "Save Snip As", default_filename, "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        if dialog.exec() == QFileDialog.Accepted:
            selected = dialog.selectedFiles()
            if selected and selected[0]:
                self._crop_pixmap.save(selected[0])
                self.btn_save.setEnabled(False)
                self.status.setStyleSheet("color: #188038; font-weight: 600;")
                self.status.setText("✓ Saved successfully")
                QTimer.singleShot(800, self.close)

    def _on_cancel(self):
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_cancel()

    def closeEvent(self, event):
        # Safely detach threads to prevent C++ destruction crashes
        if self._ocr_thread and self._ocr_thread.isRunning():
            try:
                self._ocr_thread.done.disconnect()
            except Exception:
                pass
            self._ocr_thread.wait(250)

        if self._search_thread and self._search_thread.isRunning():
            try:
                self._search_thread.done.disconnect()
            except Exception:
                pass
            self._search_thread.wait(250)

        self.closed.emit()
        super().closeEvent(event)
