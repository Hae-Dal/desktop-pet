"""행동 상태.

새 행동 추가 방법 (예: 춤추기)
    1. 이 폴더에 dance.py를 만들고 State 또는 TimedState를 상속한 클래스를 작성
       (name / animation을 정하고, config에 지속 시간이 필요하면 pet/config.py에 추가.
        프레임 속도는 frame_every로 정하며, 생략하면 config.frame_every를 씀.
        TimedState를 상속하면 클릭·메뉴 점프도 자동으로 가능)
    2. 아래 STATE_CLASSES에 등록
    3. transitions.py의 TRANSITION_WEIGHTS에 어떤 상태에서 어떤 확률로 넘어올지 추가
    4. sprites/<캐릭터>/dance_1.png ... 를 넣는다 (없으면 idle 이미지로 대체됨)
"""
from typing import Dict, List, Type

from pet.core.context import PetContext
from pet.core.states.base import State, StateMachine, TimedState
from pet.core.states.drag import DragState
from pet.core.states.fall import FallState
from pet.core.states.idle import IdleState
from pet.core.states.sit import SitState
from pet.core.states.sleep import SleepState
from pet.core.states.walk import WalkState

STATE_CLASSES: List[Type[State]] = [
    IdleState, WalkState, SitState, SleepState, FallState, DragState,
]


def build_states(ctx: PetContext) -> Dict[str, State]:
    return {cls.name: cls(ctx) for cls in STATE_CLASSES}


__all__ = ["State", "TimedState", "StateMachine", "STATE_CLASSES", "build_states"]
