"""우클릭 메뉴의 크기·조용히 하기, 설정 창 이미지 끌어다 놓기."""
import time

import pytest
from PyQt5.QtCore import QMimeData, Qt, QUrl
from PyQt5.QtGui import QColor, QDropEvent, QPixmap
from PyQt5.QtWidgets import QMenu, QMessageBox

from pet import __version__
from pet.config import PetConfig
from pet.ui import menu, prefs
from pet.ui.pet_widget import PetWidget
from pet.ui.settings import SettingsDialog, images
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


@pytest.fixture
def char_root(tmp_path, qapp):
    (tmp_path / "a").mkdir()
    pix = QPixmap(40, 20)
    pix.fill(QColor("blue"))
    pix.save(str(tmp_path / "a" / "idle.png"))
    return tmp_path


@pytest.fixture
def make_pet(qapp, char_root):
    prefs.set_check_updates(False)
    prefs.set_last_seen_version(__version__)
    pets = []

    def make():
        config = PetConfig(character="a", sprites_root=str(char_root))
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


def item(items, label):
    return [i for i in items if i.label.startswith(label)][0]


# ---------- 크기 ----------
def test_size_menu_resizes_and_is_remembered(make_pet):
    pet = make_pet()
    sizes = item(menu.default_items(pet), "크기").children
    assert [i.label for i in sizes if i.checked] == ["보통"]
    bottom = pet.ctx.y + pet.ctx.height
    item(sizes, "아주 크게").callback()
    assert (pet.width(), pet.height()) == (80, 40) and prefs.scale() == 2.0
    assert pet.ctx.y + pet.ctx.height == bottom                     # 발 위치 그대로
    assert [i.label for i in item(menu.default_items(pet), "크기").children if i.checked] == ["아주 크게"]

    again = make_pet()                                              # 다음에 켜도 유지
    assert (again.width(), again.height()) == (80, 40)


def test_size_stays_when_changing_character(make_pet, char_root):
    pet = make_pet()
    pet.set_scale(0.75)
    (char_root / "b").mkdir()
    pix = QPixmap(20, 20)
    pix.fill(QColor("red"))
    pix.save(str(char_root / "b" / "idle.png"))
    pet.change_character("b")
    assert (pet.width(), pet.height()) == (15, 15)


def test_broken_saved_size_means_normal(qapp):
    prefs.store().setValue("scale", "big")
    assert prefs.scale() == 1.0
    prefs.store().setValue("scale", -1)
    assert prefs.scale() == 1.0


def test_menu_fill_makes_submenus_and_checks(make_pet):
    pet = make_pet()
    qmenu = QMenu()
    menu.fill(qmenu, menu.default_items(pet))
    size_menu = [a for a in qmenu.actions() if a.text() == "크기"][0].menu()
    assert [a.text() for a in size_menu.actions() if a.isChecked()] == ["보통"]


# ---------- 조용히 하기 ----------
def test_quiet_for_a_while(make_pet, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    pet = make_pet()
    pet.ctx.say("말하는 중", 100)
    item(item(menu.default_items(pet), "조용히 하기").children, "30분").callback()
    assert pet.ctx.bubble_text == ""
    pet.ctx.react_line("click")
    assert pet.ctx.bubble_text == ""
    pet.ctx.notify("안내", 10)                     # 프로그램 안내는 보임
    assert pet.ctx.bubble_text == "안내"
    for _ in range(10):
        pet.ctx.tick_bubble()

    now[0] += 10 * 60
    quiet = item(menu.default_items(pet), "조용히 하는 중")
    assert quiet.label == "조용히 하는 중 (20분 남음)"
    now[0] += 20 * 60
    assert item(menu.default_items(pet), "조용히 하기")
    pet.ctx.say("다시", 10)
    assert pet.ctx.bubble_text == "다시"


def test_talk_again_ends_quiet(make_pet):
    pet = make_pet()
    pet.ctx.be_quiet(3600)
    item(item(menu.default_items(pet), "조용히 하는 중").children, "다시 말하기").callback()
    pet.ctx.say("안녕", 10)
    assert pet.ctx.bubble_text == "안녕"


def test_sleeping_while_quiet_shows_no_zzz(make_pet):
    pet = make_pet()
    pet.ctx.be_quiet(3600)
    pet.machine.change("sleep")
    assert pet.ctx.bubble_text == ""


# ---------- 끌어다 놓기 ----------
def drop(panel, widget, path):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    pos = widget.mapTo(panel, widget.rect().center())
    event = QDropEvent(pos, Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    panel.dropEvent(event)
    return event


def opened(root):
    d = SettingsDialog(str(root), "a", lambda name: None)
    d.show()
    return d, d.images


def test_drop_image_on_a_row(char_root, tmp_path):
    src = tmp_path / "new_walk.png"
    QPixmap(10, 10).save(str(src))
    d, panel = opened(char_root)
    drop(panel, panel._previews["walk"], src)
    assert panel.pending[str(char_root / "a")]["walk"] == str(src).replace("\\", "/")
    d._apply()
    assert (char_root / "a" / "walk.png").exists()
    d.close()


def test_drop_on_row_label_and_buttons_too(char_root, tmp_path):
    src = tmp_path / "x.png"
    QPixmap(10, 10).save(str(src))
    d, panel = opened(char_root)
    label = panel._grid.itemAtPosition(1, 0).widget()               # '걷기' 글자
    drop(panel, label, src)
    button = panel._grid.itemAtPosition(3, 3).widget()              # '앉기' 지우기 버튼
    drop(panel, button, src)
    assert set(panel.pending[str(char_root / "a")]) == {"walk", "sit"}
    d.close()


def test_drop_rejects_non_images_and_too_large(char_root, tmp_path, monkeypatch):
    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warned.append(args[2]))
    (tmp_path / "note.txt").write_text("x")
    d, panel = opened(char_root)
    drop(panel, panel._previews["walk"], tmp_path / "note.txt")
    assert not panel.pending and not warned
    monkeypatch.setattr(images, "MAX_PIXELS", 5)
    big = tmp_path / "big.png"
    QPixmap(10, 10).save(str(big))
    drop(panel, panel._previews["walk"], big)
    assert not panel.pending and "너무 큽니다" in warned[0]
    d.close()


def test_dropped_image_check():
    mime = QMimeData()
    assert images._dropped_image(mime) is None
    mime.setUrls([QUrl.fromLocalFile("C:/a/b.GIF")])
    assert images._dropped_image(mime) == "C:/a/b.GIF"
    mime.setUrls([QUrl.fromLocalFile("C:/a/b.png"), QUrl.fromLocalFile("C:/a/c.png")])
    assert images._dropped_image(mime) is None
    mime.setUrls([QUrl("https://example.com/x.png")])
    assert images._dropped_image(mime) is None
