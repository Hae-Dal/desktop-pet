"""설정값 모음. 숫자를 바꾸고 싶으면 이 파일만 보면 됩니다."""
import json
import os
import sys
from dataclasses import dataclass, field, fields, replace
from typing import Dict, Optional, Tuple

FROZEN = getattr(sys, "frozen", False)     # PyInstaller로 만든 exe로 실행 중

# 사용자 파일(sprites/)이 있는 폴더. 소스로 실행하면 main.py가 있는 폴더, exe면 exe가 있는 폴더.
PROJECT_DIR = (os.path.dirname(sys.executable) if FROZEN
               else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 함께 묶인 읽기 전용 파일(CHANGELOG.md)이 있는 폴더. exe면 실행 중 풀리는 임시 폴더.
BUNDLE_DIR = getattr(sys, "_MEIPASS", PROJECT_DIR)
# exe 안에 숨겨 둔 캐릭터(이스터에그). 찾으면 sprites/로 꺼내 씀. 소스로 실행하면 없음
BUNDLED_SPRITES_DIR = os.path.join(BUNDLE_DIR, "bundled_sprites")

# 상황별 기본 대사. 캐릭터가 그 상황 대사를 따로 정하지 않았거나 비워 두면 이걸 씀.
# 새 상황을 만들려면 여기에 이름을 추가하고, 그 상황에서 ctx.say_line("이름")을 부르면 됩니다.
DEFAULT_LINES: Dict[str, Tuple[str, ...]] = {
    "idle": ("심심해~", "뭐 하고 있어?", "배고프다...", "산책 갈까?"),   # 가만히 있다가 혼잣말
}

# 행동이 끝났을 때 다음 행동을 고르는 가중치. 숫자가 클수록 자주 선택되고, 0이면 안 함.
# 캐릭터는 character.json의 "transitions"에 바꿀 칸만 적으면 됩니다 (예: 잠꾸러기 {"idle": {"sleep": 3}}).
# 등록되지 않은 상태 이름이 나오면 StateMachine이 기본 상태(idle)로 대체합니다.
DEFAULT_TRANSITIONS: Dict[str, Dict[str, float]] = {
    "idle": {"walk": 3, "sit": 1, "sleep": 0.5, "jump": 0.5},
    "walk": {"idle": 1, "jump": 0.3},
    "sit": {"idle": 2, "sleep": 1},
    "sleep": {"idle": 1},
}


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
    lines: Dict[str, Tuple[str, ...]] = field(default_factory=dict)   # 상황 -> 대사 (없는 상황은 DEFAULT_LINES)

    # --- 성격 ---
    transitions: Dict[str, Dict[str, float]] = field(default_factory=dict)  # 바꿀 가중치만 (나머지는 DEFAULT_TRANSITIONS)

    @property
    def character_dir(self) -> str:
        return os.path.join(self.sprites_root, self.character)

    def lines_for(self, situation: str) -> Tuple[str, ...]:
        """그 상황에서 할 대사 목록. 캐릭터가 정한 게 없거나 비었으면 기본 대사."""
        return self.lines.get(situation) or DEFAULT_LINES.get(situation, ())

    def transitions_for(self, state: str) -> Dict[str, float]:
        """state가 끝났을 때 다음 행동 가중치 (기본값에 캐릭터 설정을 덮어씀)."""
        return {**DEFAULT_TRANSITIONS.get(state, {}), **self.transitions.get(state, {})}

    def with_character_settings(self) -> "PetConfig":
        """캐릭터 폴더의 character.json 값으로 덮어쓴 설정을 돌려줌 (파일이 없거나 깨졌으면 그대로).

        예: {"faces_left": true, "max_size": 160, "frame_every": 4,
             "lines": {"idle": ["물범아 놀자!", "졸려..."]},
             "transitions": {"idle": {"sleep": 3}}}
        """
        data = read_character_file(self.character_dir)
        if "lines" in data:
            data["lines"] = {k: tuple(v) for k, v in data["lines"].items()}
        allowed = {f.name for f in fields(self)} - {"character", "sprites_root"}
        unknown = set(data) - allowed
        if unknown:
            print(f"{self.character_dir}: character.json의 모르는 설정 무시 {sorted(unknown)}", file=sys.stderr)
        values = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items() if k in allowed}
        return replace(self, **values)


_DEFAULTS = PetConfig()
CHARACTER_FILE = "character.json"


class CharacterFileError(Exception):
    """character.json을 읽을 수 없음 (JSON 형식 오류 등)."""


def read_character_file(char_dir: str) -> Dict:
    """캐릭터 폴더의 character.json 내용 (없으면 빈 dict). 예전 형식은 지금 형식으로 바꿔서 돌려줌.

    손으로 고친 파일의 실수 하나로 프로그램이 켜지지 않거나 멈추지 않도록,
    읽을 수 없는 파일은 없는 것처럼 빈 dict를, 형식이 틀린 값은 뺀 dict를 돌려줌 (경고만 출력).
    읽을 수 없는 이유는 character_file_error로 알 수 있음.
    character.json은 여기서만 읽습니다. 쓰는 곳은 pet/ui/characters.py의 write_settings 하나.
    """
    try:
        data = _load(char_dir)
    except CharacterFileError as e:
        print(e, file=sys.stderr)
        return {}
    return _clean(data, char_dir)


def character_file_error(char_dir: str) -> Optional[str]:
    """character.json을 읽을 수 없으면 그 이유 (파일이 없거나 괜찮으면 None)."""
    try:
        _load(char_dir)
    except CharacterFileError as e:
        return str(e)
    return None


def _load(char_dir: str) -> Dict:
    path = os.path.join(char_dir, CHARACTER_FILE)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:      # JSON 형식 오류, UTF-8이 아닌 파일도 ValueError
        raise CharacterFileError(f"{path}: 읽을 수 없음 ({e})") from e
    if not isinstance(data, dict):
        raise CharacterFileError(f"{path}: {{ }}로 감싼 형식이 아님")
    if "idle_lines" in data and isinstance(data.get("lines", {}), dict):   # 0.9 이하 형식
        data.setdefault("lines", {}).setdefault("idle", data.pop("idle_lines"))
    return data


_BAD = object()


def _clean(data: Dict, where: str) -> Dict:
    """PetConfig에 있는 설정 중 형식이 틀린 값은 빼거나 고침 (모르는 설정은 그대로 둠)."""
    clean, ignored = {}, []
    for key, value in data.items():
        fixed = _fix(key, value) if hasattr(_DEFAULTS, key) else value
        if fixed is not _BAD:
            clean[key] = fixed
        if fixed is _BAD or fixed != value:
            ignored.append(key)
    if ignored:
        print(f"{where}: character.json의 형식이 틀린 값 무시 {ignored}", file=sys.stderr)
    return clean


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fix(key: str, value):
    """기본값과 같은 형식이면 value (일부만 틀렸으면 그 부분을 뺀 것), 아니면 _BAD."""
    default = getattr(_DEFAULTS, key)
    if key == "lines":                      # {"상황": ["대사", ...]}
        if not isinstance(value, dict):
            return _BAD
        return {k: [t for t in v if isinstance(t, str)] for k, v in value.items() if isinstance(v, list)}
    if key == "transitions":                # {"지금 행동": {"다음 행동": 가중치}}
        if not isinstance(value, dict):
            return _BAD
        return {state: {n: float(w) for n, w in weights.items() if _is_number(w)}
                for state, weights in value.items() if isinstance(weights, dict)}
    if isinstance(default, bool):
        return value if isinstance(value, bool) else _BAD
    if _is_number(default):
        return value if _is_number(value) else _BAD
    if isinstance(default, str):
        return value if isinstance(value, str) else _BAD
    if isinstance(default, tuple):          # (최소, 최대) 같은 숫자 묶음
        ok = isinstance(value, list) and len(value) == len(default) and all(map(_is_number, value))
        return value if ok else _BAD
    return value
