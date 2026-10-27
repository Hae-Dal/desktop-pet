from pet.core.states.fall import FallState


class JumpState(FallState):
    """스스로 점프. 위로 속도를 준 뒤 착지까지는 FallState와 같음."""
    name = "jump"
    animation = "fall"          # 클릭 점프와 같은 이미지 (fall.png, 없으면 idle)

    def enter(self) -> None:
        ctx = self.ctx
        was_walking = ctx.animation == "walk"     # super().enter()가 애니메이션을 바꾸기 전에 확인
        super().enter()
        ctx.vy = ctx.config.jump_power
        ctx.vx = ctx.facing * ctx.config.jump_forward_speed if was_walking else 0.0
