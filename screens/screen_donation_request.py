import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QCoreApplication, QEvent
from ui_components.ui_base_full import UIBaseFull
from ui_components.ui_title_text import UITitleText
from ui_components.ui_header_text import UIHeaderText
from ui_components.ui_image import UIImage
from ui_components.ui_button import UIButton



class ResizeHandler(QObject):
    def __init__(self, overlay, img_label, buttons):
        super().__init__(overlay)
        self.overlay = overlay
        self.img_label = img_label
        self.buttons = buttons

    def eventFilter(self, obj, event):
        if obj is self.overlay and event.type() == QEvent.Resize:
            self.position_elements()
        return False

    def position_elements(self):
        W = self.overlay.width()
        H = self.overlay.height()
        pix = self.img_label.pixmap()
        if pix:
            pix_h = pix.height()
            pix_y = (H - pix_h) // 2
            bottom = pix_y + pix_h
        else:
            bottom = H // 2
        spacing = 10
        for btn in self.buttons:
            btn.adjustSize()
        widths = [btn.width() for btn in self.buttons]
        total_width = sum(widths) + spacing * (len(self.buttons) - 1)
        x = (W - total_width) // 2
        y = bottom + 50
        for btn, w in zip(self.buttons, widths):
            btn.move(x, y)
            x += w + spacing

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    base = UIBaseFull()
    overlay = base.primary_overlay
    UITitleText(
        "Consider Donating",
        parent=overlay
    )
    UIHeaderText(
        "After using Talon, if you like it, consider donating. Thanks.",
        parent=overlay
    )
    img_label = UIImage("donation_request.png", parent=overlay)
    img_label.lower()
    buttons = []
    def ok_cb():
        QCoreApplication.quit()
    btn_ok = UIButton("Okay, I Will Consider It", (255, 255, 255), parent=overlay)
    btn_ok.clicked.connect(ok_cb)
    buttons.append(btn_ok)
    handler = ResizeHandler(overlay, img_label, buttons)
    overlay.installEventFilter(handler)
    handler.position_elements()
    for b in buttons:
        b.raise_()
    base.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
