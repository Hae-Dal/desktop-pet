"""펫의 '현재 상태 값'을 담는 객체.

위치, 속도, 방향, 재생 중인 애니메이션, 말풍선 내용을 한곳에 모아서
상태 클래스가 Qt 위젯을 몰라도 동작하게 합니다.
"""
import random
from typing import TYPE_CHECKING

from pet.config import PetConfig

if TYPE_CHECKING:                       # 타입 표기용. 실행 시에는 ui를 import하지 않음
    from pet.ui.world import World


class PetContext:
    def __init__(self, config: PetConfig, world: "World", width: int, height: int):
        self.config = config
        self.world = world
        self.width = width
        self.height = height

        self.x = 0
        self.y = 0
        self.vy = 0.0
        self.vx = 0.0              # 공중에서의 가로 속도 (걷다가 점프할 때)
        self.facing = 1            # 1: 오른쪽, -1: 왼쪽

        self.animation = "idle"    # 재생할 애니메이션 이름
        self.frame_idx = 0

        self.bubble_text = ""      # 말풍선 내용 (빈 문자열이면 숨김)
        self.bubble_ticks = 0      # 말풍선이 남은 tick 수

    # ---------- 위치 ----------
    @property
    def ground_y(self) -> int:
        return self.world.ground_y(self.x, self.y, self.width, self.height)

    @property
    def on_ground(self) -> bool:
        return self.vy == 0 and self.y >= self.ground_y

    def snap_to_ground(self) -> None:
        self.y = self.ground_y

    # ---------- 애니메이션 ----------
    def set_animation(self, name: str) -> None:
        if name != self.animation:
            self.animation = name
            self.frame_idx = 0

    # ---------- 말풍선 ----------
    def say(self, text: str, ticks: int = 90) -> None:
        self.bubble_text = text
        self.bubble_ticks = ticks

    def say_line(self, situation: str, ticks: int = 90) -> None:
        """그 상황의 대사 중 하나를 무작위로 말함 (대사가 없으면 아무것도 안 함)."""
        lines = self.config.lines_for(situation)
        if lines:
            self.say(random.choice(lines), ticks)

    def clear_bubble(self) -> None:
        self.bubble_text = ""
        self.bubble_ticks = 0

    def tick_bubble(self) -> None:
        if self.bubble_ticks > 0:
            self.bubble_ticks -= 1
            if self.bubble_ticks == 0:
                self.bubble_text = ""
