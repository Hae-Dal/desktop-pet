"""캐릭터 이미지 로딩.

sprites/<character>/ 폴더 안의 파일 이름으로 애니메이션을 자동 인식합니다.

    walk_1.png, walk_2.png, ...   -> "walk" 애니메이션 (번호의 숫자 크기순)
    idle.png                      -> "idle" 애니메이션 (1장)
    sit.gif                       -> "sit" 애니메이션 (움직이는 GIF·WebP는 모든 프레임)

형식은 EXTENSIONS에 있는 것만 읽습니다 (JPG·BMP는 투명 배경이 없음).
이름은 소문자로 통일하고(Walk_1.PNG -> "walk"), 같은 이름이 여러 형식으로 있으면
번호 붙은 파일 > 번호 없는 파일 중 EXTENSIONS 순서가 앞선 것 하나만 씁니다.
새 행동용 이미지를 추가하려면 `<이름>_N.png` 또는 `<이름>.gif`로 넣기만 하면 됩니다.
없는 애니메이션을 요청받으면 "idle"로 대체됩니다.

주의: QPixmap은 QApplication을 만든 뒤에 생성해야 하므로 load()는 그 이후에 호출하세요.
"""
import os
import re
from typing import Dict, List, NamedTuple, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QMovie, QPainter, QPixmap, QTransform

from pet.config import PetConfig

EXTENSIONS = ("png", "webp", "gif", "jpg", "jpeg", "bmp")    # 번호 없는 파일끼리는 이 순서로 고름
ANIMATED = ("gif", "webp")                                   # 한 파일에 여러 프레임이 있을 수 있는 형식

# <이름>[_번호].<확장자>  (이름에 '_'를 써도 됨: sleep_left_1.png -> "sleep_left", 대소문자 무시)
_FILE_RE = re.compile(r"^([a-z]+(?:_[a-z]+)*)(?:_(\d+))?\.(%s)$" % "|".join(EXTENSIONS), re.IGNORECASE)


class SpriteFile(NamedTuple):
    number: Optional[int]       # walk_3.png -> 3, idle.png -> None
    ext: str                    # "png", "gif", ... (소문자)
    path: str


def _scale(pix: QPixmap, max_size: int) -> QPixmap:
    if max(pix.width(), pix.height()) > max_size:
        return pix.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pix


def _flip(pix: QPixmap) -> QPixmap:
    return pix.transformed(QTransform().scale(-1, 1))


def scan_directory(directory: str) -> Dict[str, List[SpriteFile]]:
    """폴더 안의 이미지 파일을 애니메이션 이름(소문자)별로 묶음."""
    if not os.path.isdir(directory):
        return {}
    found: Dict[str, List[SpriteFile]] = {}
    for filename in os.listdir(directory):
        m = _FILE_RE.match(filename)
        if m:
            name, number, ext = m.groups()
            found.setdefault(name.lower(), []).append(SpriteFile(
                int(number) if number else None, ext.lower(), os.path.join(directory, filename)))
    return found


def pick_files(files: List[SpriteFile]) -> List[SpriteFile]:
    """한 동작의 파일들 중 실제로 쓸 것: 번호 붙은 파일들(번호순), 없으면 번호 없는 파일 하나."""
    numbered = sorted((f for f in files if f.number is not None), key=lambda f: f.number)
    single = sorted((f for f in files if f.number is None), key=lambda f: EXTENSIONS.index(f.ext))
    return numbered or single[:1]


def _read_frames(f: SpriteFile) -> List[QPixmap]:
    """번호 없는 GIF·WebP는 모든 프레임, 그 외(번호 붙은 파일 포함)는 한 장."""
    if f.number is None and f.ext in ANIMATED:
        movie = QMovie(f.path)
        frames = []
        for i in range(movie.frameCount()):
            movie.jumpToFrame(i)
            frames.append(movie.currentPixmap())
        if frames:
            return frames
    pix = QPixmap(f.path)
    return [] if pix.isNull() else [pix]


def _load_animation(files: List[SpriteFile], max_size: int) -> List[QPixmap]:
    return [_scale(pix, max_size) for f in pick_files(files) for pix in _read_frames(f)]


def _make_placeholder() -> Dict[str, List[QPixmap]]:
    """이미지가 없을 때 쓰는 동그란 임시 캐릭터."""
    walk = []
    for step in range(2):
        pix = QPixmap(80, 80)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffcc33"))
        p.drawEllipse(10, 10, 60, 55)           # 몸
        p.setBrush(QColor("#222222"))
        p.drawEllipse(46, 28, 8, 8)             # 눈 (오른쪽을 보는 방향)
        p.setBrush(QColor("#e05050"))
        p.drawEllipse(52, 42, 8, 8)             # 볼
        p.setBrush(QColor("#cc9900"))
        off = 5 if step == 0 else -5
        p.drawEllipse(24 + off, 60, 14, 14)     # 발
        p.drawEllipse(44 - off, 60, 14, 14)
        p.end()
        walk.append(pix)
    return {"walk": walk, "idle": [walk[0]]}


class SpriteSet:
    """애니메이션 이름 -> 프레임 목록. 좌우 반전본을 미리 만들어 둡니다."""

    def __init__(self, animations: Dict[str, List[QPixmap]]):
        animations = {k: v for k, v in animations.items() if v}
        if not animations:
            animations = _make_placeholder()
        if "idle" not in animations:
            first = animations.get("walk") or next(iter(animations.values()))
            animations["idle"] = [first[0]]

        self._right = animations
        self._left = {name: [_flip(p) for p in frames] for name, frames in animations.items()}

        all_frames = [p for frames in animations.values() for p in frames]
        self.size: Tuple[int, int] = (
            max(p.width() for p in all_frames),
            max(p.height() for p in all_frames),
        )

    @classmethod
    def load(cls, config: PetConfig) -> "SpriteSet":
        animations = {
            name: _load_animation(files, config.max_size)
            for name, files in scan_directory(config.character_dir).items()
        }
        if config.faces_left:               # 오른쪽 보는 이미지 기준으로 맞춤
            animations = {name: [_flip(p) for p in frames] for name, frames in animations.items()}
        return cls(animations)

    def has(self, name: str) -> bool:
        return name in self._right

    def frame(self, name: str, index: int, facing: int) -> QPixmap:
        table = self._right if facing >= 0 else self._left
        frames = table.get(name) or table["idle"]
        return frames[index % len(frames)]
