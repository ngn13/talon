import os
import sys
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap
from utilities.util_load_font import load_font
from utilities.util_error_popup import show_error_popup



class UIImage(QLabel):
    
    def __init__(
        self,
        filename: str,
        parent=None,
        horizontal_buffer: float = 0.3
    ):
        load_font("chakra_petch_regular.ttf")
        super().__init__("", parent)
        self.setAlignment(Qt.AlignCenter)
        if not (0.0 <= horizontal_buffer < 0.5):
            show_error_popup(
                f"Invalid horizontal_buffer: {horizontal_buffer}\n"
                "Must be between 0.0 and 0.5 (exclusive).",
                allow_continue=False
            )
            return
        self.buffer = horizontal_buffer
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            comp_dir = os.path.dirname(os.path.abspath(__file__))
            base = os.path.dirname(comp_dir)
        img_path = os.path.join(base, "media", filename)
        pix = QPixmap(img_path)
        if pix.isNull():
            show_error_popup(f"Image not found:\n{img_path}", allow_continue=False)
            return
        self._original = pix
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
            parent.installEventFilter(self)
        self._update_pixmap()

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Resize:
            self.setGeometry(0, 0, obj.width(), obj.height())
            self._update_pixmap()
        return super().eventFilter(obj, event)

    def _update_pixmap(self):
        parent = self.parent()
        if not parent:
            return
        W = parent.width()
        H = parent.height()
        avail_w = int(W * (1 - 2 * self.buffer))
        avail_h = H
        orig = self._original
        ow, oh = orig.width(), orig.height()
        scale = min(avail_w / ow, avail_h / oh)
        nw, nh = int(ow * scale), int(oh * scale)
        scaled = orig.scaled(nw, nh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)
