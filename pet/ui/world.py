"""화면 경계와 바닥 좌표 계산을 한곳에 모았습니다.

멀티 모니터나 작업표시줄 위치 대응이 필요하면 이 파일만 고치면 됩니다.
"""
import random
from typing import Tuple

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication


class World:
    def area(self) -> QRect:
        """캐릭터가 움직일 수 있는 영역 (작업표시줄 제외)."""
        return QApplication.primaryScreen().availableGeometry()

    def ground_y(self, height: int) -> int:
        """높이 height인 캐릭터가 바닥에 서 있을 때의 창 y 좌표."""
        return self.area().bottom() - height + 1

    def x_range(self, width: int) -> Tuple[int, int]:
        """너비 width인 캐릭터가 가질 수 있는 창 x 좌표 범위 (min, max)."""
        a = self.area()
        return a.left(), max(a.left(), a.right() - width + 1)

    def random_x(self, width: int) -> int:
        lo, hi = self.x_range(width)
        return random.randint(lo, hi)
