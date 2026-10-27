from typing import Optional

from pet.core.states.base import State


class FallState(State):
    """점프하거나 드래그 후 놓았을 때: 중력으로 바닥까지."""
    name = "fall"
    animation = "fall"          # 이미지가 없으면 idle로 대체됨

    def update(self) -> Optional[str]:
        ctx = self.ctx
        ctx.x += int(ctx.vx)
        lo, hi = ctx.world.x_range(ctx.width)     # 화면 밖에 놓였으면 안쪽으로 끌어옴
        ctx.x = max(lo, min(ctx.x, hi))
        ctx.vy += ctx.config.gravity
        ctx.y += int(ctx.vy)
        if ctx.y >= ctx.ground_y and ctx.vy >= 0:
            ctx.snap_to_ground()
            ctx.vy = 0
            ctx.vx = 0.0
            return "idle"
        return None
