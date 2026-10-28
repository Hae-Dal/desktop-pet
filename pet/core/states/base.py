"""상태 기반 클래스와 상태 머신."""
import random
from abc import ABC, abstractmethod
from typing import Dict, Optional

from pet.core.context import PetContext


class State(ABC):
    name: str = ""               # 상태 이름 (레지스트리 키)
    animation: str = "idle"      # 재생할 애니메이션 이름
    frame_every: Optional[int] = None   # 몇 tick마다 프레임을 넘길지 (None이면 config.frame_every)

    def __init__(self, ctx: PetContext):
        self.ctx = ctx
        self._anim_tick = 0
        if self.frame_every is None:
            self.frame_every = ctx.config.frame_every

    def enter(self) -> None:
        self.ctx.set_animation(self.animation)
        self._anim_tick = 0

    def exit(self) -> None:
        pass

    @abstractmethod
    def update(self) -> Optional[str]:
        """매 tick 호출. 다른 상태로 넘어가려면 그 상태 이름을 반환."""

    def advance_animation(self) -> None:
        if self.frame_every:
            self._anim_tick += 1
            if self._anim_tick % self.frame_every == 0:
                self.ctx.frame_idx += 1


class TimedState(State):
    """바닥에서 일정 시간 지속되다가 가중치 표에 따라 다음 상태로 넘어가는 상태."""
    duration_range = (60, 120)

    def enter(self) -> None:
        super().enter()
        self._remaining = random.randint(*self.duration_range)

    def update(self) -> Optional[str]:
        ctx = self.ctx
        if ctx.y < ctx.ground_y:       # 공중에 떠 있으면 떨어뜨림
            return "fall"
        ctx.snap_to_ground()

        self.act()

        self._remaining -= 1
        if self._remaining <= 0:
            return _pick(self.ctx.config.transitions_for(self.name))
        return None

    def act(self) -> None:
        """매 tick 하는 동작 (하위 클래스에서 구현)."""


def _pick(weights: Dict[str, float]) -> Optional[str]:
    """가중치대로 하나 고름 (가중치가 모두 0이거나 없으면 None = 지금 행동 계속)."""
    names = [n for n, w in weights.items() if w > 0]
    if not names:
        return None
    return random.choices(names, weights=[weights[n] for n in names])[0]


class StateMachine:
    def __init__(self, states: Dict[str, State], default: str = "idle"):
        self.states = states
        self.default = default
        self.current: Optional[State] = None

    @property
    def current_name(self) -> str:
        return self.current.name if self.current else ""

    def change(self, name: str) -> None:
        if name not in self.states:
            name = self.default
        if self.current:
            self.current.exit()
        self.current = self.states[name]
        self.current.enter()

    def update(self) -> None:
        if self.current is None:
            self.change(self.default)
        next_name = self.current.update()
        self.current.advance_animation()
        if next_name:
            self.change(next_name)
