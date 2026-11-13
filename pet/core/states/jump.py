from typing import Optional

from pet.core.states.fall import FallState


class JumpState(FallState):
    """점프. 위로 속도를 준 뒤 착지까지는 FallState와 같음.

    올라가는 동안은 jump 이미지, 꼭대기를 지나 내려올 때는 fall 이미지
    (둘 중 하나만 있으면 그 이미지로 둘 다, 둘 다 없으면 idle).
    """
    name = "jump"
    animation = "jump"

    def update(self) -> Optional[str]:
        next_name = super().update()
        if self.ctx.vy >= 0:
            self.ctx.set_animation("fall")
        return next_name

    def enter(self) -> None:
        ctx = self.ctx
        was_walking = ctx.animation == "walk"     # super().enter()가 애니메이션을 바꾸기 전에 확인
        super().enter()
        ctx.vy = ctx.config.jump_power
        ctx.vx = ctx.facing * ctx.config.jump_forward_speed if was_walking else 0.0
