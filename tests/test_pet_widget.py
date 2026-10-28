"""펫 창: 클릭·드래그·메뉴·이스터에그·캐릭터 바꾸기."""
import pytest
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtGui import QColor, QMouseEvent, QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from pet import config as config_module
from pet.config import PetConfig
from pet.ui import characters, menu, pet_widget, prefs
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


@pytest.fixture
def make_pet(qapp, monkeypatch):
    prefs.set_check_updates(False)   # 테스트 중 인터넷 확인 안 함
    pets = []

    def make(config=None):
        config = config or PetConfig()
        pet = pet_widget.PetWidget(config, SpriteSet.load(config), World())
        pet.show()
        pets.append(pet)
        return pet

    yield make
    for pet in pets:
        pet.bubble.close()
        pet.close()


def ticks(pet, n):
    for _ in range(n):
        pet._timer.timeout.emit()


def test_starts_on_the_ground(make_pet):
    pet = make_pet()
    assert pet.ctx.y == pet.ctx.ground_y and pet.machine.current_name == "idle"


def test_click_jumps(make_pet):
    pet = make_pet()
    QTest.mouseClick(pet, Qt.LeftButton, pos=QPoint(10, 10))
    assert pet.machine.current_name == "fall" and pet.ctx.vy < 0


def test_menu_jump(make_pet):
    pet = make_pet()
    jump = [i for i in menu.default_items(pet) if i.label == "점프"][0]
    jump.callback()
    assert pet.ctx.vy < 0


def test_click_wakes_sleeping_pet(make_pet):
    pet = make_pet()
    pet.machine.change("sleep")
    QTest.mousePress(pet, Qt.LeftButton, pos=QPoint(10, 10))
    assert pet.ctx.bubble_text == "으앗! 깜짝이야"
    QTest.mouseRelease(pet, Qt.LeftButton, pos=QPoint(10, 10))


def mouse(pet, kind, pos, buttons=Qt.LeftButton):
    """QTest.mouseMove는 버튼을 누른 채 움직이는 걸 표현하지 못해 직접 보냄."""
    event = QMouseEvent(kind, pos, pet.mapToGlobal(pos), Qt.LeftButton, buttons, Qt.NoModifier)
    QApplication.sendEvent(pet, event)


def test_drag_moves_then_falls(make_pet):
    pet = make_pet()
    start = pet.pos()
    mouse(pet, QEvent.MouseButtonPress, QPoint(10, 10))
    for step in range(1, 6):        # 펫이 따라 움직이므로 펫 기준 좌표는 매번 같은 만큼씩
        mouse(pet, QEvent.MouseMove, QPoint(10 + 10, 10 - 20))
    mouse(pet, QEvent.MouseButtonRelease, QPoint(10, 10), Qt.NoButton)
    assert pet.machine.current_name == "fall" and pet.ctx.y < start.y()
    for _ in range(200):                # 착지한 순간을 확인 (그 뒤엔 스스로 점프할 수도 있음)
        ticks(pet, 1)
        if pet.machine.current_name != "fall":
            break
    assert pet.machine.current_name == "idle" and pet.ctx.y == pet.ctx.ground_y


def test_update_menu_item_only_when_new_version(make_pet):
    pet = make_pet()
    assert not any("새 버전" in i.label for i in menu.default_items(pet))
    pet._on_update_available("9.9.9", "http://x")
    assert any(i.label == "새 버전 받기 (v9.9.9)" for i in menu.default_items(pet))


def test_change_character_resizes(make_pet, tmp_path):
    pix = QPixmap(60, 30)
    pix.fill(QColor("blue"))
    (tmp_path / "wide").mkdir()
    pix.save(str(tmp_path / "wide" / "idle.png"))
    pet = make_pet(PetConfig(sprites_root=str(tmp_path)))
    pet.change_character("wide")
    assert (pet.width(), pet.height()) == (60, 30) and pet.config.character == "wide"


@pytest.fixture
def bundled_egg(tmp_path, monkeypatch):
    """exe 안에 숨겨 둔 이스터에그 캐릭터 흉내."""
    bundled = tmp_path / "bundled"
    egg = bundled / characters.EASTER_EGG
    egg.mkdir(parents=True)
    pix = QPixmap(20, 20)
    pix.fill(QColor("gray"))
    pix.save(str(egg / "idle.png"))
    monkeypatch.setattr(config_module, "BUNDLED_SPRITES_DIR", str(bundled))
    root = tmp_path / "sprites"
    root.mkdir()
    return root


def test_easter_egg_after_fast_clicks(make_pet, bundled_egg, monkeypatch):
    pet = make_pet(PetConfig(sprites_root=str(bundled_egg)))
    for _ in range(pet.config.easter_egg_clicks - 1):
        QTest.mouseClick(pet, Qt.LeftButton, pos=QPoint(5, 5))
    assert pet.config.character == "default"
    QTest.mouseClick(pet, Qt.LeftButton, pos=QPoint(5, 5))
    assert pet.config.character == characters.EASTER_EGG
    assert prefs.easter_egg_unlocked() and prefs.active_character() == characters.EASTER_EGG
    assert (bundled_egg / characters.EASTER_EGG / "idle.png").exists()      # sprites/로 꺼내 둠


def test_slow_clicks_do_not_find_easter_egg(make_pet, bundled_egg, monkeypatch):
    import time
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    pet = make_pet(PetConfig(sprites_root=str(bundled_egg)))
    for _ in range(pet.config.easter_egg_clicks * 2):
        now[0] += pet.config.easter_egg_seconds / 2
        QTest.mouseClick(pet, Qt.LeftButton, pos=QPoint(5, 5))
    assert pet.config.character == "default"
