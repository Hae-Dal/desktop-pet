"""공통 준비: 화면 없이 Qt 실행, 테스트가 실제 사용자 설정(레지스트리 등)을 바꾸지 않게 보호.

    pip install -r requirements-dev.txt
    python -m pytest
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setOrganizationName("desktop_pet")
    app.setApplicationName("desktop_pet")
    return app


@pytest.fixture(autouse=True)
def keep_user_settings():
    """테스트는 빈 저장값에서 시작하고, 끝나면 사용자의 원래 값을 되돌려 놓음."""
    store = QSettings("desktop_pet", "desktop_pet")
    saved = {k: store.value(k) for k in store.allKeys()}
    store.clear()
    yield
    store.clear()
    for k, v in saved.items():
        store.setValue(k, v)
    store.sync()


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
