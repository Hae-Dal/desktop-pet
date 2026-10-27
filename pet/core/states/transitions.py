"""상태 전환 가중치 표. 행동 확률을 바꾸려면 이 파일만 고치면 됩니다."""
import random
from typing import Dict, Optional

# 타이머가 끝났을 때 다음 상태로 넘어갈 가중치. 숫자가 클수록 자주 선택됨.
# 등록되지 않은 상태 이름이 나오면 StateMachine이 기본 상태(idle)로 대체합니다.
TRANSITION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "idle": {"walk": 3, "sit": 1, "sleep": 0.5, "jump": 0.5},
    "walk": {"idle": 1, "jump": 0.3},
    "sit": {"idle": 2, "sleep": 1},
    "sleep": {"idle": 1},
}


def pick_next(current: str) -> Optional[str]:
    weights = TRANSITION_WEIGHTS.get(current)
    if not weights:
        return None
    names = list(weights)
    return random.choices(names, weights=[weights[n] for n in names])[0]
