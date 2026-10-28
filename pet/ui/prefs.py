"""앱이 기억해 두는 값. 저장 항목은 모두 여기서만 읽고 씁니다.

저장 위치는 QSettings가 정합니다 (Windows는 레지스트리, macOS/Linux는 설정 파일).
캐릭터 모양·대사 같은 캐릭터별 설정은 여기가 아니라 캐릭터 폴더의 character.json에 있습니다.
"""
from typing import Optional

from PyQt5.QtCore import QSettings

ORGANIZATION = APPLICATION = "desktop_pet"

_CHARACTER = "character"                # 마지막으로 고른 캐릭터
_EASTER_EGG = "unlocked_easter_egg"     # 숨은 캐릭터를 찾았는지
_CHECK_UPDATES = "check_updates"        # 새 버전 확인 켜기/끄기
_LAST_SEEN_VERSION = "last_seen_version"


def store() -> QSettings:
    return QSettings(ORGANIZATION, APPLICATION)


def active_character() -> Optional[str]:
    return store().value(_CHARACTER)


def set_active_character(name: str) -> None:
    store().setValue(_CHARACTER, name)


def easter_egg_unlocked() -> bool:
    return store().value(_EASTER_EGG, False, type=bool)


def unlock_easter_egg() -> None:
    store().setValue(_EASTER_EGG, True)


def check_updates() -> bool:
    return store().value(_CHECK_UPDATES, True, type=bool)


def set_check_updates(on: bool) -> None:
    store().setValue(_CHECK_UPDATES, on)


def last_seen_version() -> Optional[str]:
    return store().value(_LAST_SEEN_VERSION)


def set_last_seen_version(version: str) -> None:
    store().setValue(_LAST_SEEN_VERSION, version)
