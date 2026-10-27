"""설정값 모음. 숫자를 바꾸고 싶으면 이 파일만 보면 됩니다."""
import os
from dataclasses import dataclass
from typing import Tuple

# 프로젝트 루트 (main.py가 있는 폴더). 이 파일은 pet/ 안에 있으므로 한 단계 위.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class PetConfig:
    # --- 캐릭터 ---
    character: str = "default"                      # sprites/<character>/ 폴더 이름
    sprites_root: str = os.path.join(PROJECT_DIR, "sprites")
    max_size: int = 128                             # 캐릭터 최대 크기(px), 넘으면 축소

    # --- 루프 ---
    tick_ms: int = 30                               # 갱신 주기(ms)

    # --- 이동 / 물리 ---
    speed: int = 2                                  # 걷는 속도 (px / tick)
    gravity: float = 1.2
    jump_power: float = -14.0
    jump_forward_speed: float = 3.0                 # 걷다가 점프할 때 앞으로 나가는 속도 (px / tick)

    # --- 애니메이션 ---
    frame_every: int = 8                            # 기본 프레임 전환 간격 (상태별로 따로 정하지 않은 경우)
    walk_frame_every: int = 5                       # 몇 tick마다 걷기 프레임을 넘길지
    sleep_frame_every: int = 20                     # 잠자기 이미지가 여러 장일 때 프레임 전환 간격

    # --- 상태 지속 시간 (tick 단위, (최소, 최대)) ---
    idle_ticks: Tuple[int, int] = (40, 120)
    walk_ticks: Tuple[int, int] = (60, 200)
    sit_ticks: Tuple[int, int] = (80, 200)
    sleep_ticks: Tuple[int, int] = (200, 500)

    # --- 말풍선 ---
    idle_chat_chance: float = 0.3                   # idle 상태로 들어갈 때 혼잣말할 확률
    idle_lines: Tuple[str, ...] = ("심심해~", "뭐 하고 있어?", "배고프다...", "산책 갈까?")

    @property
    def character_dir(self) -> str:
        return os.path.join(self.sprites_root, self.character)
