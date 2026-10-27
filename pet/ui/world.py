"""화면 경계와 바닥 좌표 계산을 한곳에 모았습니다.

모니터가 여러 개면 전체를 하나의 영역으로 보고 넘나들 수 있게 하되,
바닥 높이는 캐릭터가 지금 서 있는 모니터(작업표시줄 제외) 기준으로 계산합니다.
"""
import random
from typing import List, Tuple

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication


class World:
    def screens(self) -> List[QRect]:
        """모니터별 사용 가능 영역 (작업표시줄 제외)."""
        return [s.availableGeometry() for s in QApplication.screens()]

    def area(self) -> QRect:
        """모든 모니터를 합친 영역."""
        rect = QRect()
        for r in self.screens():
            rect = rect.united(r)
        return rect

    def area_at(self, x: int, y: int, width: int, height: int) -> QRect:
        """캐릭터 중심이 속한 모니터 영역. 모니터 사이 틈이면 가장 가까운 모니터."""
        cx, cy = x + width // 2, y + height // 2
        screens = self.screens()
        column = [r for r in screens if r.left() <= cx <= r.right()]
        if not column:
            return min(screens, key=lambda r: min(abs(cx - r.left()), abs(cx - r.right())))
        for r in column:
            if r.top() <= cy <= r.bottom():
                return r
        below = [r for r in column if r.top() > cy]       # 위아래로 쌓인 모니터: 아래쪽으로 떨어짐
        if below:
            return min(below, key=lambda r: r.top())
        return max(column, key=lambda r: r.bottom())

    def ground_y(self, x: int, y: int, width: int, height: int) -> int:
        """(x, y)에 있는 캐릭터가 바닥에 서 있을 때의 창 y 좌표."""
        return self.area_at(x, y, width, height).bottom() - height + 1

    def x_range(self, width: int) -> Tuple[int, int]:
        """너비 width인 캐릭터가 가질 수 있는 창 x 좌표 범위 (min, max)."""
        a = self.area()
        return a.left(), max(a.left(), a.right() - width + 1)

    def random_x(self, width: int) -> int:
        """시작 위치는 주 모니터 안에서 고름."""
        a = QApplication.primaryScreen().availableGeometry()
        return random.randint(a.left(), max(a.left(), a.right() - width + 1))
