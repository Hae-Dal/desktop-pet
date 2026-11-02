"""트레이 아이콘, 숨기기, 컴퓨터를 켜면 같이 시작."""
import sys

import pytest
from PyQt5.QtWidgets import QCheckBox

from pet.config import PetConfig
from pet.ui import autostart, menu, prefs, tray
from pet.ui.pet_widget import PetWidget
from pet.ui.settings import SettingsDialog
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


@pytest.fixture
def make_pet(qapp, monkeypatch):
    prefs.set_check_updates(False)
    pets = []

    def make(has_tray=True):
        monkeypatch.setattr(tray, "available", lambda: has_tray)
        config = PetConfig()
        pet = PetWidget(config, SpriteSet.load(config), World())
        pet.show()
        pets.append(pet)
        return pet

    yield make
    for pet in pets:
        if pet.tray:
            pet.tray.hide()
        pet.bubble.close()
        pet.close()


def labels(items):
    return [i.label for i in items]


def test_hide_and_show_again(make_pet):
    pet = make_pet()
    assert "숨기기" in labels(menu.default_items(pet))
    pet.ctx.say("안녕", 100)
    pet.toggle_hidden()
    assert not pet.isVisible() and not pet.bubble.isVisible() and not pet._timer.isActive()
    assert labels(menu.tray_items(pet))[0] == "보이기"
    x = pet.ctx.x
    pet.tray._on_activated(tray.QSystemTrayIcon.Trigger)        # 아이콘 왼쪽 클릭
    assert pet.isVisible() and pet._timer.isActive() and pet.ctx.x == x
    assert labels(menu.tray_items(pet))[0] == "숨기기"


def test_running_again_shows_hidden_pet(make_pet):
    pet = make_pet()
    pet.toggle_hidden()
    pet.greet()
    assert pet.isVisible() and pet.ctx.bubble_text == "나 이미 여기 있어!"


def test_no_hide_menu_without_tray(make_pet):
    pet = make_pet(has_tray=False)
    assert pet.tray is None and "숨기기" not in labels(menu.default_items(pet))


def test_tray_menu_has_common_items(make_pet):
    pet = make_pet()
    assert labels(menu.tray_items(pet)) == ["숨기기", "설정...", "업데이트 내역", "종료"]
    pet.tray._fill_menu()
    assert [a.text() for a in pet.tray._menu.actions()] == labels(menu.tray_items(pet))


def test_autostart_register_and_remove(qapp):
    assert not autostart.is_enabled()
    autostart.set_enabled(True)
    assert autostart.is_enabled()
    assert autostart._store().value(autostart.NAME) == f'"{sys.executable}"'
    autostart.set_enabled(False)
    assert not autostart.is_enabled() and not autostart._store().contains(autostart.NAME)


def test_autostart_follows_moved_exe(qapp):
    autostart.follow_moved_exe()
    assert not autostart._store().contains(autostart.NAME)          # 꺼 둔 사람은 그대로
    autostart._store().setValue(autostart.NAME, '"C:/old/DesktopPet.exe"')
    autostart.follow_moved_exe()
    assert autostart.is_enabled()


def autostart_box(d):
    return [b for b in d.findChildren(QCheckBox) if b.text().startswith("컴퓨터를 켜면")][0]


def test_settings_checkbox(tmp_path, qapp, monkeypatch):
    (tmp_path / "a").mkdir()
    d = SettingsDialog(str(tmp_path), "a", lambda name: None)
    assert not autostart_box(d).isEnabled()                         # 소스로 실행 중이면 못 씀

    monkeypatch.setattr(autostart, "supported", lambda: True)
    d = SettingsDialog(str(tmp_path), "a", lambda name: None)
    box = autostart_box(d)
    assert box.isEnabled() and not box.isChecked()
    box.setChecked(True)
    d._apply()
    assert autostart.is_enabled()
    box.setChecked(False)
    d._apply()
    assert not autostart.is_enabled()
