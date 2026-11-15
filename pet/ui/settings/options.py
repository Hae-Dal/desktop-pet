"""설정 창의 캐릭터별 설정 칸: '옵션', '성격', '대사'.

모든 칸을 같은 방식으로 다룹니다.
    load(values)    기본값 + character.json + 아직 적용 안 한 변경을 합친 값을 칸에 보여 줌
    changes(saved)  지금 칸 내용 중 character.json(saved)과 달라진 값만 돌려줌
값 하나짜리 칸은 _Field로 연결하고 load_fields / changed_fields로 다룹니다 (사용자가 건드리지 않은 값은 쓰지 않음).
"""
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from pet.config import DEFAULT_LINES, PetConfig

# 프레임 간격: (설정 이름, 표시 이름). tick 단위로 저장하고 ms로 보여 줌
FRAME_OPTIONS = [
    ("frame_every", "기본 프레임 간격"),
    ("walk_frame_every", "걷기 프레임 간격"),
    ("sleep_frame_every", "잠자기 프레임 간격"),
]

# 대사 칸에서 고를 수 있는 상황: (상황 이름, 표시 이름). 순서대로 표시됨 (DEFAULT_LINES의 상황을 모두 적음)
LINE_SITUATIONS = [
    ("idle", "혼잣말"),
    ("lonely", "오래 안 만졌을 때"),
    ("click", "클릭했을 때"),
    ("grab", "잡아서 끌 때"),
    ("drop", "끌다가 놓았을 때"),
    ("sleep", "자는 동안"),
    ("woken", "자다가 클릭으로 깼을 때"),
    ("wake", "스스로 일어났을 때"),
    ("morning", "아침에 켰을 때 (5~11시)"),
    ("afternoon", "낮에 켰을 때 (11~17시)"),
    ("evening", "저녁에 켰을 때 (17~22시)"),
    ("night", "밤에 켰을 때 (22~5시)"),
]

# 성격 칸: 자주 하는 정도를 고를 행동 (행동 이름, 표시 이름)
OFTEN_BEHAVIORS = [
    ("walk", "걷기"),
    ("sit", "앉기"),
    ("sleep", "잠자기"),
    ("jump", "점프"),
]
# 슬라이더 칸마다의 (배수, 표시 이름). 왼쪽부터 순서대로
OFTEN_LEVELS = [(0, "안 함"), (0.5, "가끔"), (1, "보통"), (2, "자주"), (4, "아주 자주")]
SPEED_RANGE = (1, 8)

_DEFAULTS = PetConfig()


def _often_level(multiplier: float) -> int:
    """배수에 가장 가까운 슬라이더 칸 (손으로 적은 값이 칸과 딱 맞지 않아도 됨)."""
    return min(range(len(OFTEN_LEVELS)), key=lambda i: abs(OFTEN_LEVELS[i][0] - multiplier))


def _same(value):
    return value


@dataclass
class _Field:
    """설정 값 하나와 칸 하나의 연결.

    show:  파일 값 -> 칸에 보일 값 (단위 바꾸기, 칸 범위로 자르기)
    store: 칸 값 -> 파일에 쓸 값
    칸 값이 show(파일 값)과 같으면 사용자가 건드리지 않은 것이므로 파일에 쓰지 않음.
    그래서 칸 범위를 넘거나 칸 단위로 딱 떨어지지 않는 값을 손으로 적어 두어도 그대로 남음.
    """
    key: str                            # 설정 이름
    get: Callable[[], Any]
    set: Callable[[Any], None]
    show: Callable[[Any], Any]
    store: Callable[[Any], Any] = _same
    sub: Optional[str] = None           # dict 설정(often)의 한 칸이면 그 안의 이름
    sub_default: Any = None             # 그 이름이 dict에 없을 때의 값

    def file_value(self, values: Dict):
        if self.sub is None:
            return values.get(self.key, getattr(_DEFAULTS, self.key))
        return values.get(self.key, {}).get(self.sub, self.sub_default)


def _checkbox_field(key: str, box: QCheckBox) -> _Field:
    return _Field(key, box.isChecked, box.setChecked, bool)


def _number_field(key: str, widget, to_shown: Callable[[float], float] = _same,
                  store: Callable[[int], Any] = _same, **sub) -> _Field:
    """QSpinBox·QSlider 칸: 파일 값을 칸 단위로 바꾼 뒤 칸 범위 안으로."""
    def show(value) -> int:
        shown = to_shown(value)
        if not math.isfinite(shown):        # JSON의 Infinity·NaN
            return widget.maximum() if shown > 0 else widget.minimum()
        return max(widget.minimum(), min(round(shown), widget.maximum()))
    return _Field(key, widget.value, widget.setValue, show, store, **sub)


def load_fields(fields: List[_Field], values: Dict) -> None:
    for f in fields:
        f.set(f.show(f.file_value(values)))


def changed_fields(fields: List[_Field], saved: Dict) -> Dict:
    """칸 값이 파일 값(saved)을 보여 준 값과 다른 설정만 (dict 설정은 바꾸지 않은 칸도 유지)."""
    changed: Dict = {}
    for f in fields:
        value = f.get()
        if value == f.show(f.file_value(saved)):
            continue
        if f.sub is None:
            changed[f.key] = f.store(value)
        else:
            changed.setdefault(f.key, dict(saved.get(f.key, {})))[f.sub] = f.store(value)
    return changed


def _shown_lines(lines: Dict, situation: str) -> List[str]:
    """그 상황에서 칸에 보여 줄 대사 (정한 게 없거나 비었으면 기본 대사)."""
    return list(lines.get(situation) or DEFAULT_LINES[situation])


class OptionsPanel(QGroupBox):
    def __init__(self):
        super().__init__("옵션")
        form = QFormLayout(self)
        self.faces_left = QCheckBox("이미지 속 캐릭터가 왼쪽을 봄")
        form.addRow(self.faces_left)
        self.max_size = QSpinBox()
        self.max_size.setRange(16, 1024)
        self.max_size.setSuffix(" px")
        form.addRow("최대 크기:", self.max_size)
        self._fields = [_checkbox_field("faces_left", self.faces_left),
                        _number_field("max_size", self.max_size)]
        tick = _DEFAULTS.tick_ms
        for name, label in FRAME_OPTIONS:
            spin = QSpinBox()
            spin.setRange(tick, tick * 100)
            spin.setSingleStep(tick)
            spin.setSuffix(" ms")
            form.addRow(label + ":", spin)
            self._fields.append(_number_field(name, spin, lambda v: v * tick,
                                              lambda ms: max(1, round(ms / tick))))

    def load(self, values: Dict) -> None:
        load_fields(self._fields, values)

    def changes(self, saved: Dict) -> Dict:
        return changed_fields(self._fields, saved)


class PersonalityPanel(QGroupBox):
    def __init__(self):
        super().__init__("성격")
        form = QFormLayout(self)
        self._often: Dict[str, QSlider] = {}
        self._fields: List[_Field] = []
        for name, label in OFTEN_BEHAVIORS:
            row, slider = _slider_row(0, len(OFTEN_LEVELS) - 1, lambda i: OFTEN_LEVELS[i][1])
            form.addRow(label + ":", row)
            self._often[name] = slider
            self._fields.append(_number_field("often", slider, _often_level, lambda i: OFTEN_LEVELS[i][0],
                                              sub=name, sub_default=1))
        row, self.speed = _slider_row(*SPEED_RANGE, str)
        form.addRow("걷는 속도:", row)
        self._fields.append(_number_field("speed", self.speed))

    def load(self, values: Dict) -> None:
        load_fields(self._fields, values)

    def changes(self, saved: Dict) -> Dict:
        return changed_fields(self._fields, saved)


def _slider_row(lo: int, hi: int, describe: Callable[[int], str]) -> Tuple[QWidget, QSlider]:
    """오른쪽에 현재 값 이름이 보이는 가로 슬라이더: (폼에 넣을 줄, 슬라이더)."""
    row = QWidget()
    slider = QSlider(Qt.Horizontal, row)
    slider.setRange(lo, hi)
    slider.setPageStep(1)
    value = QLabel(describe(lo), row)
    value.setMinimumWidth(value.fontMetrics().boundingRect("아주 자주").width() + 4)
    slider.valueChanged.connect(lambda v: value.setText(describe(v)))
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(slider, 1)
    layout.addWidget(value)
    return row, slider


class LinesPanel(QGroupBox):
    def __init__(self):
        super().__init__("대사")
        self._texts: Dict[str, List[str]] = {}      # 상황 -> 칸의 대사 (아직 적용 안 한 변경 포함)
        self.situation = QComboBox()
        for name, label in LINE_SITUATIONS:
            self.situation.addItem(label, name)
        self._shown_situation = self.situation.currentData()
        self.situation.currentIndexChanged.connect(self._show_situation)
        self.list = QListWidget()
        add = QPushButton("추가")
        add.clicked.connect(self._add)
        remove = QPushButton("삭제")
        remove.clicked.connect(self._remove)
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        self.chance = QSpinBox()
        self.chance.setRange(0, 100)
        self.chance.setSuffix(" %")
        self._fields = [_number_field("idle_chat_chance", self.chance, lambda v: v * 100, lambda p: p / 100)]
        chance_row = QFormLayout()
        chance_row.addRow("말할 확률:", self.chance)
        note = QLabel("두 번 클릭하면 고칠 수 있어요.\n모두 지우면 기본 대사로 돌아갑니다.\n"
                      "혼자 하는 말은 이 확률로, 만지거나 켰을 때는 항상 말해요.\n0%면 말하지 않아요.")
        note.setEnabled(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.situation)
        layout.addWidget(self.list)
        layout.addLayout(buttons)
        layout.addLayout(chance_row)
        layout.addWidget(note)

    def load(self, values: Dict) -> None:
        load_fields(self._fields, values)
        self._texts = {name: _shown_lines(values["lines"], name) for name, _ in LINE_SITUATIONS}
        self._fill_list()

    def changes(self, saved: Dict) -> Dict:
        changed = changed_fields(self._fields, saved)
        self._texts[self._shown_situation] = self.texts()
        saved_lines = saved.get("lines", {})
        edited = {name: texts for name, texts in self._texts.items()
                  if texts != _shown_lines(saved_lines, name)}
        if edited:
            changed["lines"] = {**saved_lines, **edited}    # 바꾸지 않은 상황은 그대로 둠
        return changed

    def _show_situation(self) -> None:
        self._texts[self._shown_situation] = self.texts()
        self._shown_situation = self.situation.currentData()
        self._fill_list()

    def _fill_list(self) -> None:
        self.list.clear()
        for text in self._texts[self._shown_situation]:
            self._append(text)

    def texts(self) -> List[str]:
        """대사 칸 내용 (빈 줄은 뺌). 비어 있으면 기본 대사를 쓰라는 뜻."""
        texts = (self.list.item(i).text().strip() for i in range(self.list.count()))
        return [t for t in texts if t]

    def _append(self, text: str) -> QListWidgetItem:
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.list.addItem(item)
        return item

    def _add(self) -> None:
        item = self._append("")
        self.list.setCurrentItem(item)
        self.list.editItem(item)

    def _remove(self) -> None:
        row = self.list.currentRow()
        if row >= 0:
            self.list.takeItem(row)
