from typing import Optional

from pet.core.states.base import State


class DragState(State):
    """마우스로 잡고 있는 동안. 위치는 위젯이 직접 갱신합니다."""
    name = "drag"
    animation = "drag"          # 이미지가 없으면 idle로 대체됨

    def enter(self) -> None:
        super().enter()
        self.ctx.vy = 0

    def update(self) -> Optional[str]:
        return None
