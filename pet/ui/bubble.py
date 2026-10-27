"""말풍선. 펫과 별개의 투명 창이 펫 머리 위를 따라다닙니다."""
from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygon
from PyQt5.QtWidgets import QWidget

PAD = 8                 # 글자와 테두리 사이 여백
TAIL = 8                # 말풍선 꼬리 높이
MAX_TEXT_WIDTH = 160    # 이보다 길면 줄바꿈
GAP = 2                 # 펫과 말풍선 사이 간격


class BubbleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            | Qt.WindowTransparentForInput          # 클릭이 말풍선을 통과함
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._font = QFont("Malgun Gothic", 10)
        self._text = ""

    def set_text(self, text: str) -> None:
        if text == self._text:
            return
        self._text = text
        rect = QFontMetrics(self._font).boundingRect(
            QRect(0, 0, MAX_TEXT_WIDTH, 1000), Qt.TextWordWrap, text)
        self.resize(rect.width() + PAD * 2, rect.height() + PAD * 2 + TAIL)
        self.update()

    def follow(self, pet_rect: QRect, area: QRect) -> None:
        """펫 머리 위 중앙에 배치하되 화면 밖으로 나가지 않게 보정."""
        x = pet_rect.center().x() - self.width() // 2
        y = pet_rect.top() - self.height() - GAP
        x = max(area.left(), min(x, area.right() - self.width() + 1))
        y = max(area.top(), y)
        self.move(x, y)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        body = QRect(1, 1, self.width() - 2, self.height() - TAIL - 2)
        cx = self.width() // 2
        border = QColor("#555555")

        p.setPen(QPen(border, 1.5))
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(body, 8, 8)

        # 꼬리: 흰 삼각형으로 몸통 경계선을 지우고, 양쪽 변만 선을 그림
        b = body.bottom()
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygon([QPoint(cx - 6, b), QPoint(cx + 6, b), QPoint(cx, self.height() - 1)]))
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.drawLine(cx - 5, b, cx + 5, b)
        p.setPen(QPen(border, 1.5))
        p.drawLine(cx - 6, b, cx, self.height() - 1)
        p.drawLine(cx + 6, b, cx, self.height() - 1)

        p.setPen(QColor("#222222"))
        p.setFont(self._font)
        p.drawText(QRect(PAD, PAD, self.width() - PAD * 2, self.height() - PAD * 2 - TAIL),
                   Qt.AlignCenter | Qt.TextWordWrap, self._text)
