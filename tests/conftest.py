"""공통 준비: 화면 없이 Qt 실행, 테스트가 실제 사용자 설정(레지스트리 등)을 바꾸지 않게 보호.

    pip install -r requirements-dev.txt
    python -m pytest
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt5.QtWidgets import QApplication

from pet import __version__
from pet.config import PetConfig
from pet.ui import autostart, prefs, tray
from pet.ui.pet_widget import PetWidget
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setOrganizationName(prefs.ORGANIZATION)
    app.setApplicationName(prefs.APPLICATION)
    return app


@pytest.fixture(autouse=True)
def separate_settings(tmp_path, monkeypatch):
    """테스트마다 빈 임시 파일에 저장. 사용자의 실제 저장값(레지스트리 등)은 읽지도 쓰지도 않음."""
    monkeypatch.setattr(prefs, "override_file", str(tmp_path / "prefs.ini"))
    monkeypatch.setattr(autostart, "override_file", str(tmp_path / "autostart.ini"))   # 시작 프로그램 등록도


@pytest.fixture
def make_pet(qapp, monkeypatch):
    """펫 창을 만드는 함수. 테스트가 끝나면 모두 닫음.

    인터넷 새 버전 확인은 끄고, '업데이트됐어' 안내가 대사를 막지 않게 이번 버전을 본 것으로 해 둠.
    has_tray를 정하면 트레이를 쓸 수 있는지를 그 값으로 바꿈 (None이면 실제 환경대로).
    """
    prefs.set_check_updates(False)
    prefs.set_last_seen_version(__version__)
    pets = []

    def make(config=None, has_tray=None):
        if has_tray is not None:
            monkeypatch.setattr(tray, "available", lambda: has_tray)
        config = config or PetConfig()
        pet = PetWidget(config, SpriteSet.load(config, prefs.scale()), World())
        pet.show()
        pets.append(pet)
        return pet

    yield make
    for pet in pets:
        if pet.tray:
            pet.tray.hide()
        pet.bubble.close()
        pet.close()


class FakeWorld:
    """화면 하나짜리 가짜 세상: x는 0~width, 바닥은 ground."""

    def __init__(self, width: int = 1000, ground: int = 500):
        self.width, self.ground = width, ground

    def ground_y(self, x, y, w, h):
        return self.ground - h

    def x_range(self, w):
        return 0, self.width - w


@pytest.fixture
def world():
    return FakeWorld()
