from typing import Optional

from pet.core.context import PetContext
from pet.core.states.base import TimedState


class SleepState(TimedState):
    name = "sleep"
    animation = "sleep"         # 이미지가 없으면 idle로 대체됨

    def __init__(self, ctx: PetContext):
        super().__init__(ctx)
        self.duration_range = ctx.config.sleep_ticks
        self.frame_every = ctx.config.sleep_frame_every

    def enter(self) -> None:
        super().enter()
        self._slept_enough = False
        self.ctx.say_line("sleep", self._remaining)     # 자는 동안 계속 표시

    def update(self) -> Optional[str]:
        next_name = super().update()
        self._slept_enough = next_name is not None and self._remaining <= 0
        return next_name

    def exit(self) -> None:
        self.ctx.clear_bubble()
        if self._slept_enough:                          # 깨운 게 아니라 스스로 일어났을 때
            self.ctx.chat_line("wake")
