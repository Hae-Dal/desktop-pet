"""이스터에그: 펫을 빠르게 연타하면 숨은 캐릭터가 나타납니다.

숨은 캐릭터 이미지는 exe 안(config.BUNDLED_SPRITES_DIR)에 들어 있다가, 찾으면 sprites/로 꺼냅니다.
찾기 전에는 설정 창 목록에 보이지 않습니다 (characters.list_characters).
"""
import os
import shutil
import time
from typing import List

from pet import config
from pet.ui import prefs
from pet.ui.sprites import scan_directory

NAME = "seal_girl"


class RapidClicks:
    """seconds 안에 count번 클릭했는지 셈."""

    def __init__(self, count: int, seconds: float):
        self.count, self.seconds = count, seconds
        self._times: List[float] = []

    def click(self) -> bool:
        """클릭 한 번 기록. 조건을 채웠으면 True (그리고 처음부터 다시 셈)."""
        now = time.monotonic()
        self._times = [t for t in self._times if now - t <= self.seconds] + [now]
        if len(self._times) >= self.count:
            self._times.clear()
            return True
        return False


def available(sprites_root: str) -> bool:
    """sprites/ 또는 exe 안에 숨은 캐릭터 이미지가 있는지 (소스로 실행하고 이미지가 없으면 False)."""
    return any(scan_directory(os.path.join(base, NAME))
               for base in (sprites_root, config.BUNDLED_SPRITES_DIR))


def reveal(sprites_root: str) -> None:
    """찾았음: exe 안의 이미지를 sprites/로 꺼내고(이미 있으면 그대로), 찾은 것과 사용 중인 캐릭터로 기록."""
    src = os.path.join(config.BUNDLED_SPRITES_DIR, NAME)
    dst = os.path.join(sprites_root, NAME)
    if not os.path.isdir(dst) and os.path.isdir(src):
        shutil.copytree(src, dst)
    prefs.unlock_easter_egg()
    prefs.set_active_character(NAME)
