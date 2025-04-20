""" Import necessary modules for the program to work """
import sys
import os
from components.resource_utils import get_resource_path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QApplication
)
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer

class InstallScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Talon Installer")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowState(Qt.WindowFullScreen | Qt.WindowActive)
        self.load_chakra_petch_font()
        self.create_screen_overlays()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("Installing Talon...")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        title_label.setFont(QFont("Chakra Petch", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        body_label = QLabel("This may take a few minutes. Do not turn your PC off.")
        body_label.setStyleSheet("color: white;")
        body_label.setFont(QFont("Chakra Petch", 18))
        body_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(body_label)
        layout.addSpacing(30)
        spinner_layout = QHBoxLayout()
        spinner_layout.setAlignment(Qt.AlignCenter)
        self.spinner = LoadingSpinner()
        spinner_layout.addWidget(self.spinner)
        self.spinner.start_spinning()
        layout.addLayout(spinner_layout)
        self.status_label = QLabel("Preparing installation…")
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setFont(QFont("Chakra Petch", 14))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def set_status(self, text: str):
        self.status_label.setText(text)

    """ Load the Chakra Petch font, which is used for the UI """
    def load_chakra_petch_font(self):
        font_path = get_resource_path("ChakraPetch-Regular.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Failed to load font.")
        else:
            print("Font loaded successfully.")

    """ Create overlays for other screens """
    def create_screen_overlays(self):
        app = QApplication.instance()
        screens = app.screens()
        self.overlays = []
        for screen in screens[1:]:
            overlay = QWidget()
            overlay.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            overlay.setGeometry(screen.geometry())
            overlay.setStyleSheet("background-color: black;")
            overlay.showFullScreen()
            self.overlays.append(overlay)

    """ Override the close() method to close all overlays """
    def close(self):
        for overlay in self.overlays:
            overlay.close()
        super().close()



""" Create a class for the loading spinner in the UI """
class LoadingSpinner(QFrame):

    """ Initialization """
    def __init__(self):
        super().__init__()
        self.setFixedSize(100, 100)
        self.setStyleSheet("background-color: transparent;")
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    """ Use QPainter to draw the spinner """
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(6)
        painter.setPen(pen)
        painter.setBrush(Qt.transparent)
        rect = self.rect()
        painter.drawArc(rect.adjusted(10, 10, -10, -10), self.angle * 16, 100 * 16)

    """ Begin spinning """
    def start_spinning(self):
        self.angle = 0
        self.update()

    """ Update the spinner to spin """
    def update(self):
        self.angle -= 5
        if self.angle <= -360:
            self.angle = 0
        super().update()



""" Start the program """
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallScreen()
    window.show()
    sys.exit(app.exec_())