import random

from pet.core.context import PetContext
from pet.core.states.base import TimedState


class WalkState(TimedState):
    name = "walk"
    animation = "walk"

    def __init__(self, ctx: PetContext):
        super().__init__(ctx)
        self.duration_range = ctx.config.walk_ticks
        self.frame_every = ctx.config.walk_frame_every

    def enter(self) -> None:
        super().enter()
        self.ctx.facing = random.choice([-1, 1])

    def act(self) -> None:
        ctx = self.ctx
        lo, hi = ctx.world.x_range(ctx.width)
        ctx.x += ctx.facing * ctx.config.speed
        if ctx.x <= lo:
            ctx.x = lo
            ctx.facing = 1
        elif ctx.x >= hi:
            ctx.x = hi
            ctx.facing = -1
