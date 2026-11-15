"""펫의 '현재 상태 값'을 담는 객체.

위치, 속도, 방향, 재생 중인 애니메이션, 말풍선 내용을 한곳에 모아서
상태 클래스가 Qt 위젯을 몰라도 동작하게 합니다.
"""
import random
import time
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
        self.bubble_is_notice = False   # 프로그램 안내(notify) 중이면 대사로 덮어쓰지 않음

        self.untouched_ticks = 0   # 마지막으로 만진 뒤 지난 tick 수
        self.quiet_until = 0.0     # 이 시각(time.monotonic)까지 말하지 않음 (안내는 표시)

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
    @property
    def quiet_seconds_left(self) -> float:
        return max(0.0, self.quiet_until - time.monotonic())

    def be_quiet(self, seconds: float) -> None:
        """seconds 동안 말하지 않음 (0이면 다시 말함). 지금 하던 말도 지움."""
        self.quiet_until = time.monotonic() + seconds if seconds > 0 else 0.0
        if seconds > 0:
            self.clear_bubble()

    def say(self, text: str, ticks: int = 90) -> None:
        """펫의 말. 프로그램 안내가 떠 있거나 조용히 하는 중이면 말하지 않음."""
        if not self.bubble_is_notice and not self.quiet_seconds_left:
            self.bubble_text = text
            self.bubble_ticks = ticks

    def notify(self, text: str, ticks: int = 90) -> None:
        """프로그램 안내 (새 버전 등). 끝날 때까지 대사로 덮이거나 지워지지 않음."""
        self.bubble_text = text
        self.bubble_ticks = ticks
        self.bubble_is_notice = True

    def say_line(self, situation: str, ticks: int = 90) -> None:
        """그 상황의 대사 중 하나를 무작위로 말함 (대사가 없으면 아무것도 안 함)."""
        lines = self.config.lines_for(situation)
        if lines:
            self.say(random.choice(lines), ticks)

    def react_line(self, situation: str, ticks: int = 90) -> None:
        """만졌을 때나 켰을 때의 대사: 항상 말함 (말할 확률이 0이면 말하지 않음)."""
        if self.config.idle_chat_chance > 0:
            self.say_line(situation, ticks)

    def chat_line(self, situation: str) -> None:
        """혼자 하는 대사: 말할 확률에 따라."""
        if random.random() < self.config.idle_chat_chance:
            self.say_line(situation)

    def chat(self) -> None:
        """혼잣말. 오래 안 만졌으면 심심하다고 하고, 다시 시간을 셈."""
        if self.untouched_ticks >= self.config.lonely_ticks:
            if random.random() < self.config.idle_chat_chance:
                self.untouched_ticks = 0
                self.say_line("lonely")
        else:
            self.chat_line("idle")

    def clear_bubble(self) -> None:
        if not self.bubble_is_notice:
            self.bubble_text = ""
            self.bubble_ticks = 0

    def tick_bubble(self) -> None:
        if self.bubble_ticks > 0:
            self.bubble_ticks -= 1
            if self.bubble_ticks == 0:
                self.bubble_text = ""
                self.bubble_is_notice = False
