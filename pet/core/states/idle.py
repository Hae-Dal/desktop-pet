import random

from pet.core.context import PetContext
from pet.core.states.base import TimedState


class IdleState(TimedState):
    name = "idle"
    animation = "idle"

    def __init__(self, ctx: PetContext):
        super().__init__(ctx)
        self.duration_range = ctx.config.idle_ticks

    def enter(self) -> None:
        super().enter()
        if self.ctx.bubble_text:            # 이미 말하는 중이면 덮어쓰지 않음
            return
        if random.random() < self.ctx.config.idle_chat_chance:
            self.ctx.say_line("idle")
