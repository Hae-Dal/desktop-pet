"""캐릭터 폴더 관리: 목록, 동작별 이미지 넣기·지우기, character.json, 사용 중인 캐릭터.

설정 창이 쓰는 파일 작업을 모아 두었습니다. 이미지 파일 이름 규칙은 sprites.py와 같습니다.
"""
import json
import os
import re
import shutil
from typing import Dict, Iterable, List, Optional

from pet import config
from pet.ui import prefs
from pet.ui.sprites import scan_directory

# 설정 창에 보여 줄 동작 (이미지 이름, 표시 이름). 순서대로 표시됨
ANIMATIONS = [
    ("idle", "가만히 있기"),
    ("walk", "걷기"),
    ("fall", "점프 · 떨어짐"),
    ("sit", "앉기"),
    ("sleep", "잠자기"),
    ("drag", "잡혔을 때"),
]

# 이스터에그: 펫을 빠르게 연타하면 나타나는 숨은 캐릭터. 찾기 전에는 설정 창 목록에 안 보임
EASTER_EGG = "seal_girl"

_INVALID_NAME = re.compile(r'[\\/:*?"<>|]|^\.|^$')


def list_characters(root: str) -> List[str]:
    """설정 창에 보여 줄 캐릭터 (찾지 않은 이스터에그 캐릭터는 뺌)."""
    if not os.path.isdir(root):
        return []
    hidden = set() if prefs.easter_egg_unlocked() else {EASTER_EGG}
    return sorted(n for n in os.listdir(root)
                  if os.path.isdir(os.path.join(root, n)) and n not in hidden)


def exists(root: str, name: str) -> bool:
    return os.path.isdir(os.path.join(root, name))


def has_images(root: str, name: str) -> bool:
    """sprites/ 또는 exe 안에 숨겨 둔 곳에 그 캐릭터 이미지가 있는지."""
    return any(scan_directory(os.path.join(base, name)) for base in (root, config.BUNDLED_SPRITES_DIR))


def install_bundled(root: str, name: str) -> None:
    """exe 안에 숨겨 둔 캐릭터를 sprites/로 꺼냄 (이미 있으면 그대로)."""
    src = os.path.join(config.BUNDLED_SPRITES_DIR, name)
    if not exists(root, name) and os.path.isdir(src):
        shutil.copytree(src, os.path.join(root, name))


def is_valid_name(name: str) -> bool:
    return not _INVALID_NAME.search(name.strip())


def create_character(root: str, name: str) -> str:
    path = os.path.join(root, name.strip())
    os.makedirs(path)
    return path


def delete_character(root: str, name: str) -> None:
    shutil.rmtree(os.path.join(root, name))


def animation_file(char_dir: str, anim: str) -> Optional[str]:
    """그 동작에 실제로 쓰이는 파일 (번호 붙은 파일 > .png > .gif). 미리보기용."""
    files = scan_directory(char_dir).get(anim, [])
    numbered = sorted((f for f in files if f.number is not None), key=lambda f: f.number)
    png = [f for f in files if f.number is None and f.ext == "png"]
    gif = [f for f in files if f.number is None and f.ext == "gif"]
    for group in (numbered, png, gif):
        if group:
            return group[0].path
    return None


def clear_animation(char_dir: str, anim: str) -> None:
    for f in scan_directory(char_dir).get(anim, []):
        os.remove(f.path)


def set_animation(char_dir: str, anim: str, src: str) -> None:
    """기존 파일을 지우고 src를 <동작>.<확장자>로 복사."""
    ext = os.path.splitext(src)[1].lower()
    with open(src, "rb") as f:             # 같은 파일을 다시 고른 경우를 위해 지우기 전에 읽음
        data = f.read()
    clear_animation(char_dir, anim)
    with open(os.path.join(char_dir, anim + ext), "wb") as f:
        f.write(data)


def read_settings(char_dir: str) -> Dict:
    path = os.path.join(char_dir, "character.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_settings(char_dir: str, values: Dict, remove: Iterable[str] = ()) -> None:
    """기존 character.json에 values를 합쳐 저장 (설정 창에 없는 값은 유지). remove의 키는 지움."""
    data = read_settings(char_dir)
    data.update(values)
    for key in remove:
        data.pop(key, None)
    with open(os.path.join(char_dir, "character.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
