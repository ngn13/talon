from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from utilities.util_load_font import load_font



class UIParagraphText(QLabel):
    def __init__(
        self,
        text: str,
        parent=None,
        font_size: int = 18,
        color: str = "#FFFFFF",
        alignment="left"
    ):
        load_font("chakra_petch_regular.ttf")
        super().__init__(parent)
        self.setWordWrap(True)
        self.setText(text)
        self.setStyleSheet(
            f"QLabel {{"
            f"  font-size: {font_size}px;"
            f"  color: {color};"
            f"  padding: 10px;"
            f"}}"
        )
        align_flag = self._parse_alignment(alignment)
        self.setAlignment(align_flag)

    @staticmethod
    def _parse_alignment(algn):
        if isinstance(algn, int):
            return Qt.Alignment(algn)
        s = str(algn).strip().lower()
        if s == "left":
            return Qt.AlignLeft | Qt.AlignTop
        if s == "center":
            return Qt.AlignHCenter | Qt.AlignTop
        if s == "right":
            return Qt.AlignRight | Qt.AlignTop
        try:
            return getattr(Qt, s)
        except Exception:
            return Qt.AlignLeft | Qt.AlignTop
