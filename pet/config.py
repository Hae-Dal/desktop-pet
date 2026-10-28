"""설정값 모음. 숫자를 바꾸고 싶으면 이 파일만 보면 됩니다."""
import json
import os
import sys
from dataclasses import dataclass, fields, replace
from typing import Tuple

FROZEN = getattr(sys, "frozen", False)     # PyInstaller로 만든 exe로 실행 중

# 사용자 파일(sprites/)이 있는 폴더. 소스로 실행하면 main.py가 있는 폴더, exe면 exe가 있는 폴더.
PROJECT_DIR = (os.path.dirname(sys.executable) if FROZEN
               else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 함께 묶인 읽기 전용 파일(CHANGELOG.md)이 있는 폴더. exe면 실행 중 풀리는 임시 폴더.
BUNDLE_DIR = getattr(sys, "_MEIPASS", PROJECT_DIR)
# exe 안에 숨겨 둔 캐릭터(이스터에그). 찾으면 sprites/로 꺼내 씀. 소스로 실행하면 없음
BUNDLED_SPRITES_DIR = os.path.join(BUNDLE_DIR, "bundled_sprites")


@dataclass
class PetConfig:
    # --- 캐릭터 ---
    character: str = "default"                      # sprites/<character>/ 폴더 이름
    sprites_root: str = os.path.join(PROJECT_DIR, "sprites")
    max_size: int = 128                             # 캐릭터 최대 크기(px), 넘으면 축소
    faces_left: bool = False                        # 이미지 속 캐릭터가 왼쪽을 보고 있으면 True

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

    # --- 이스터에그 ---
    easter_egg_clicks: int = 10                     # 이 횟수만큼
    easter_egg_seconds: float = 3.0                 # 이 시간(초) 안에 클릭하면 숨은 캐릭터 등장

    # --- 말풍선 ---
    idle_chat_chance: float = 0.3                   # idle 상태로 들어갈 때 혼잣말할 확률
    idle_lines: Tuple[str, ...] = ("심심해~", "뭐 하고 있어?", "배고프다...", "산책 갈까?")

    @property
    def character_dir(self) -> str:
        return os.path.join(self.sprites_root, self.character)

    def with_character_settings(self) -> "PetConfig":
        """캐릭터 폴더의 character.json 값으로 덮어쓴 설정을 돌려줌 (파일이 없으면 그대로).

        예: {"faces_left": true, "max_size": 160, "frame_every": 4}
        """
        path = os.path.join(self.character_dir, "character.json")
        if not os.path.isfile(path):
            return self
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        allowed = {f.name for f in fields(self)} - {"character", "sprites_root"}
        unknown = set(data) - allowed
        if unknown:
            print(f"{path}: 모르는 설정 무시 {sorted(unknown)}", file=sys.stderr)
        values = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items() if k in allowed}
        return replace(self, **values)
