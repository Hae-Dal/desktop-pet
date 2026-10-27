from pet.core.context import PetContext
from pet.core.states.base import TimedState


class SitState(TimedState):
    name = "sit"
    animation = "sit"           # 이미지가 없으면 idle로 대체됨

    def __init__(self, ctx: PetContext):
        super().__init__(ctx)
        self.duration_range = ctx.config.sit_ticks
