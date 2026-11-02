"""컴퓨터를 켜면 펫도 같이 시작 (Windows만).

현재 사용자의 '시작 프로그램' 레지스트리(Run 키)에 exe 경로를 적어 둡니다. 관리자 권한은 필요 없고,
작업 관리자 → 시작 앱에서도 보이고 끌 수 있습니다.
소스(python main.py)로 실행 중일 때는 등록할 exe가 없으므로 지원하지 않습니다.
"""
import sys
from typing import Optional

from PyQt5.QtCore import QSettings

from pet.config import FROZEN

RUN_KEY = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
NAME = "DesktopPet"

# 정해 두면 레지스트리 대신 이 ini 파일을 씀 (테스트용, prefs.override_file과 같은 방식)
override_file: Optional[str] = None


def supported() -> bool:
    return sys.platform == "win32" and FROZEN


def _store() -> QSettings:
    if override_file:
        return QSettings(override_file, QSettings.IniFormat)
    return QSettings(RUN_KEY, QSettings.NativeFormat)


def _command() -> str:
    return f'"{sys.executable}"'


def is_enabled() -> bool:
    """지금 실행 중인 이 exe가 등록돼 있는지."""
    return _store().value(NAME) == _command()


def set_enabled(on: bool) -> None:
    store = _store()
    if on:
        store.setValue(NAME, _command())
    else:
        store.remove(NAME)


def follow_moved_exe() -> None:
    """켜 두었는데 exe 위치가 바뀌었으면(새 버전을 다른 폴더에 풀었을 때 등) 지금 exe로 고침."""
    store = _store()
    if store.contains(NAME) and store.value(NAME) != _command():
        store.setValue(NAME, _command())
