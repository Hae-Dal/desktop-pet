"""캐릭터 폴더 관리와 이미지 불러오기."""
import json

import pytest
from PyQt5.QtGui import QColor, QPixmap

from pet.config import PetConfig
from pet.ui import characters, easter_egg, prefs
from pet.ui.sprites import SpriteSet, scan_directory


def png(path, w=10, h=10):
    pix = QPixmap(w, h)
    pix.fill(QColor("red"))
    assert pix.save(str(path))
    return path


@pytest.fixture
def root(tmp_path, qapp):
    for name in ("cat", easter_egg.NAME):
        (tmp_path / name).mkdir()
    return tmp_path


def test_easter_egg_hidden_until_found(root):
    assert characters.list_characters(str(root)) == ["cat"]
    prefs.unlock_easter_egg()
    assert characters.list_characters(str(root)) == sorted(["cat", easter_egg.NAME])


def test_create_and_delete(root):
    characters.create_character(str(root), " dog ")
    assert characters.exists(str(root), "dog")
    characters.delete_character(str(root), "dog")
    assert not characters.exists(str(root), "dog")


@pytest.mark.parametrize("name, ok", [("cat2", True), ("a/b", False), (".x", False), ("", False), ("고양이", True)])
def test_valid_names(name, ok):
    assert characters.is_valid_name(name) is ok


def test_set_animation_replaces_old_files(root, tmp_path_factory):
    src = png(tmp_path_factory.mktemp("src") / "anything.png")
    char = root / "cat"
    png(char / "walk_1.png")
    png(char / "walk_2.png")
    characters.set_animation(str(char), "walk", str(src))
    assert sorted(p.name for p in char.iterdir()) == ["walk.png"]
    characters.clear_animation(str(char), "walk")
    assert list(char.iterdir()) == []


def test_animation_file_priority(root):
    char = root / "cat"
    for name in ("idle.gif", "idle.png", "idle_2.png", "idle_1.png"):
        png(char / name) if name.endswith("png") else (char / name).write_bytes(b"")
    assert characters.animation_file(str(char), "idle").endswith("idle_1.png")


def test_write_settings_merges(root):
    char = str(root / "cat")
    characters.write_settings(char, {"max_size": 99})
    characters.write_settings(char, {"faces_left": True})
    assert characters.read_settings(char) == {"max_size": 99, "faces_left": True}


def test_saving_converts_old_format_file(root):
    char = root / "cat"
    (char / "character.json").write_text(json.dumps({"idle_lines": ["예전"], "speed": 3}), encoding="utf-8")
    characters.write_settings(str(char), {"max_size": 50})
    saved = json.loads((char / "character.json").read_text(encoding="utf-8"))
    assert saved == {"speed": 3, "max_size": 50, "lines": {"idle": ["예전"]}}


def test_saved_values_are_remembered(qapp):
    assert prefs.active_character() is None and prefs.check_updates() is True
    assert prefs.easter_egg_unlocked() is False
    prefs.set_active_character("cat")
    prefs.set_check_updates(False)
    assert prefs.active_character() == "cat" and prefs.check_updates() is False


def test_scan_directory_groups_by_name(tmp_path, qapp):
    for name in ("Walk_1.PNG", "walk_2.png", "sleep_left_1.png", "idle.gif", "notes.txt"):
        (tmp_path / name).write_bytes(b"")
    found = scan_directory(str(tmp_path))
    assert sorted(found) == ["idle", "sleep_left", "walk"]
    assert sorted(f.number for f in found["walk"]) == [1, 2]


def test_sprites_fallbacks(tmp_path, qapp):
    empty = SpriteSet.load(PetConfig(character="none", sprites_root=str(tmp_path)))
    assert empty.has("walk") and empty.has("idle")          # 이미지가 없으면 임시 도형
    (tmp_path / "cat").mkdir()
    png(tmp_path / "cat" / "walk_1.png", 30, 20)
    sprites = SpriteSet.load(PetConfig(character="cat", sprites_root=str(tmp_path)))
    assert sprites.size == (30, 20)
    assert sprites.frame("sleep", 0, 1).size() == sprites.frame("idle", 0, 1).size()   # 없는 동작은 idle로


def test_large_images_are_scaled_down(tmp_path, qapp):
    (tmp_path / "cat").mkdir()
    png(tmp_path / "cat" / "idle.png", 400, 200)
    (tmp_path / "cat" / "character.json").write_text(json.dumps({"max_size": 100}), encoding="utf-8")
    config = PetConfig(character="cat", sprites_root=str(tmp_path)).with_character_settings()
    assert SpriteSet.load(config).size == (100, 50)
