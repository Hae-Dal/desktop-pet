"""설정값과 캐릭터별 설정(character.json)."""
import json

from pet.config import DEFAULT_LINES, DEFAULT_TRANSITIONS, PetConfig


def make_character(tmp_path, data, name="cat"):
    folder = tmp_path / name
    folder.mkdir()
    (folder / "character.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return PetConfig(character=name, sprites_root=str(tmp_path))


def test_no_file_keeps_defaults(tmp_path):
    (tmp_path / "cat").mkdir()
    config = PetConfig(character="cat", sprites_root=str(tmp_path))
    assert config.with_character_settings() == config


def test_character_file_overrides(tmp_path):
    config = make_character(tmp_path, {"max_size": 160, "faces_left": True, "idle_ticks": [1, 2]})
    result = config.with_character_settings()
    assert result.max_size == 160 and result.faces_left is True
    assert result.idle_ticks == (1, 2)                  # 목록은 튜플로


def test_character_file_cannot_change_name_or_folder(tmp_path):
    config = make_character(tmp_path, {"character": "dog", "sprites_root": "x", "nope": 1})
    result = config.with_character_settings()
    assert result.character == "cat" and result.sprites_root == str(tmp_path)


def test_lines_default_and_custom(tmp_path):
    assert PetConfig().lines_for("idle") == DEFAULT_LINES["idle"]
    assert PetConfig().lines_for("unknown") == ()
    result = make_character(tmp_path, {"lines": {"idle": ["야옹"]}}).with_character_settings()
    assert result.lines_for("idle") == ("야옹",)


def test_empty_lines_fall_back_to_default(tmp_path):
    result = make_character(tmp_path, {"lines": {"idle": []}}).with_character_settings()
    assert result.lines_for("idle") == DEFAULT_LINES["idle"]


def test_old_idle_lines_format_still_read(tmp_path):
    result = make_character(tmp_path, {"idle_lines": ["예전 대사"]}).with_character_settings()
    assert result.lines_for("idle") == ("예전 대사",)


def test_new_lines_format_wins_over_old(tmp_path):
    data = {"idle_lines": ["예전"], "lines": {"idle": ["새것"]}}
    result = make_character(tmp_path, data).with_character_settings()
    assert result.lines_for("idle") == ("새것",)


def test_transitions_override_only_given_weights(tmp_path):
    result = make_character(tmp_path, {"transitions": {"idle": {"sleep": 3}}}).with_character_settings()
    weights = result.transitions_for("idle")
    assert weights["sleep"] == 3 and weights["walk"] == DEFAULT_TRANSITIONS["idle"]["walk"]
    assert result.transitions_for("walk") == DEFAULT_TRANSITIONS["walk"]
