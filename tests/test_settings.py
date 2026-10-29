"""설정 창: 화면에 있는 버튼·칸을 직접 눌러 보며 확인."""
import json
from pathlib import Path

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QCheckBox, QListWidget, QPushButton, QSpinBox

from pet.config import DEFAULT_LINES, PetConfig
from pet.ui import prefs
from pet.ui.settings import SettingsDialog, images


class Dialog:
    """설정 창을 사람처럼 다루는 도우미."""

    def __init__(self, root, current="a"):
        self.applied = []
        self.root = root
        self.d = SettingsDialog(str(root), current, self.applied.append)
        lists = self.d.findChildren(QListWidget)
        self.characters, self.lines = lists[0], lists[1]

    def button(self, text, nth=0):
        return [b for b in self.d.findChildren(QPushButton) if b.text() == text][nth]

    def spin(self, suffix):
        return [s for s in self.d.findChildren(QSpinBox) if s.suffix() == suffix]

    def select(self, name):
        self.characters.setCurrentItem(self.characters.findItems(name, Qt.MatchExactly)[0])

    def line_texts(self):
        return [self.lines.item(i).text() for i in range(self.lines.count())]

    def add_line(self, text):
        self.button("추가").click()
        self.lines.item(self.lines.count() - 1).setText(text)

    def apply(self):
        self.button("적용").click()

    def json(self, name):
        path = self.root / name / "character.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@pytest.fixture
def root(tmp_path, qapp):
    (tmp_path / "a").mkdir()
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "character.json").write_text(
        json.dumps({"idle_lines": ["옛날 대사"], "max_size": 99}, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_nothing_changed_writes_nothing(root):
    ui = Dialog(root)
    assert ui.line_texts() == list(DEFAULT_LINES["idle"])
    ui.apply()
    assert ui.json("a") is None and ui.applied == ["a"]


def test_lines_and_chance_are_saved(root):
    ui = Dialog(root)
    ui.add_line("  새 대사  ")
    ui.add_line("")                                  # 빈 줄은 무시
    ui.spin(" %")[0].setValue(80)
    ui.apply()
    saved = ui.json("a")
    assert saved["lines"]["idle"] == list(DEFAULT_LINES["idle"]) + ["새 대사"]
    assert saved["idle_chat_chance"] == 0.8
    config = PetConfig(character="a", sprites_root=str(root)).with_character_settings()
    assert config.lines_for("idle")[-1] == "새 대사" and config.idle_chat_chance == 0.8


def test_old_format_is_shown_and_converted(root):
    ui = Dialog(root, "old")
    assert ui.line_texts() == ["옛날 대사"]
    ui.lines.item(0).setText("고친 대사")
    ui.apply()
    assert ui.json("old") == {"max_size": 99, "lines": {"idle": ["고친 대사"]}}


def test_unsaved_edits_survive_switching_characters(root):
    ui = Dialog(root)
    ui.add_line("임시")
    ui.select("old")
    ui.select("a")
    assert ui.line_texts()[-1] == "임시"


def test_clearing_all_lines_means_default(root):
    ui = Dialog(root, "old")
    ui.lines.clear()
    ui.apply()
    config = PetConfig(character="old", sprites_root=str(root)).with_character_settings()
    assert config.lines_for("idle") == DEFAULT_LINES["idle"]


def test_options_are_saved(root):
    ui = Dialog(root)
    [c for c in ui.d.findChildren(QCheckBox) if "왼쪽" in c.text()][0].setChecked(True)
    ui.spin(" px")[0].setValue(200)
    ui.apply()
    assert ui.json("a") == {"faces_left": True, "max_size": 200}


def test_update_check_toggle(root):
    ui = Dialog(root)
    [c for c in ui.d.findChildren(QCheckBox) if "새 버전" in c.text()][0].setChecked(False)
    ui.apply()
    assert prefs.check_updates() is False


DATA = Path(__file__).parent / "data"      # anim.gif: 12x8, 3프레임


def image(path, w, h):
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(0)
    assert img.save(str(path))
    return str(path)


def test_image_check_accepts_normal_images(tmp_path, qapp):
    assert images.check_image(image(tmp_path / "ok.png", 4096, 10)) is None
    assert images.check_image(str(DATA / "anim.gif")) is None


def test_image_check_rejects_too_large(tmp_path, qapp):
    assert "너무 큽니다" in images.check_image(image(tmp_path / "wide.png", 4097, 10))
    assert "너무 큽니다" in images.check_image(image(tmp_path / "tall.bmp", 10, 5000))


def test_image_check_rejects_too_many_frames(qapp, monkeypatch):
    monkeypatch.setattr(images, "MAX_FRAMES", 2)
    assert "프레임이 너무 많습니다" in images.check_image(str(DATA / "anim.gif"))


def test_image_check_rejects_broken_file(tmp_path, qapp):
    (tmp_path / "broken.png").write_bytes(b"not a png")
    assert "읽을 수 없습니다" in images.check_image(str(tmp_path / "broken.png"))
