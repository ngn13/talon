import os
import sys
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from components.resource_utils import get_resource_path

logger = logging.getLogger(__name__)

class AnimatedButton(QPushButton):
    def __init__(self, text, color, hover_color=None):
        super().__init__(text)
        self.default_color = color
        self.hover_color = hover_color or color
        self.setStyleSheet(f"background-color: {self.default_color.name()}; color: white; border: none;")
        self.setFont(QFont("Chakra Petch", 14, QFont.Bold))
        self.setFixedSize(240, 40)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(80)
        self.shadow_effect.setColor(self.default_color.darker(200))
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)
        self.animation = QPropertyAnimation(self.shadow_effect, b"blurRadius")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.shadow_effect.blurRadius())
        self.animation.setEndValue(200)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.shadow_effect.blurRadius())
        self.animation.setEndValue(80)
        self.animation.start()
        super().leaveEvent(event)

class RavenAppScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = logger
        self.logger.info("Initializing RavenAppScreen UI")

        self.setWindowTitle("Optional: Install Raven Software")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        try:
            self.load_chakra_petch_font()
        except FileNotFoundError as e:
            self.logger.error("Font file missing: %s", e)
        except Exception as e:
            self.logger.exception("Error loading Chakra Petch font: %s", e)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Optional: Install Raven Software")
        title.setStyleSheet("color: white; font-weight: bold;")
        title.setFont(QFont("Chakra Petch", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        body = QLabel("Simple, powerful, and privacy focused. Lightweight software designed to just work, with minimal distractions and hassle.")
        body.setStyleSheet("color: white;")
        body.setFont(QFont("Chakra Petch", 16))
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body)
        image_label = QLabel(self)
        try:
            pixmap = QPixmap(get_resource_path("additional_software_offer.png"))
            scaled = pixmap.scaledToWidth(int(self.width() * 0.6), Qt.SmoothTransformation)
            image_label.setPixmap(scaled)
        except Exception as e:
            self.logger.exception("Failed to load offer image: %s", e)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        hlayout = QHBoxLayout()
        yes = AnimatedButton("Yes, Install", QColor(34, 139, 34), QColor(50, 205, 50))
        no  = AnimatedButton("No, Thanks", QColor(139, 0, 0), QColor(205, 92, 92))
        yes.clicked.connect(lambda: self.select_option(True))
        no.clicked.connect(lambda: self.select_option(False))
        hlayout.addWidget(yes)
        hlayout.addWidget(no)
        layout.addLayout(hlayout)

        self.setLayout(layout)
        self.selected_option = None

    def load_chakra_petch_font(self):
        font_path = get_resource_path("ChakraPetch-Regular.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError(font_path)
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            raise RuntimeError("QFontDatabase failed to load ChakraPetch-Regular.ttf")
        logger.info("Chakra Petch font loaded (id=%d)", font_id)

    option_selected = pyqtSignal(bool)

    def select_option(self, option: bool):
        self.selected_option = option
        logger.info("User selected Raven install: %s", "Yes" if option else "No")
        self.option_selected.emit(option)
        self.close()