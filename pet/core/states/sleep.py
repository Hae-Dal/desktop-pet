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
        self.ctx.say("Zzz...", self._remaining)     # 자는 동안 계속 표시

    def exit(self) -> None:
        self.ctx.clear_bubble()
