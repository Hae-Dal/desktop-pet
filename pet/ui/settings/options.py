"""설정 창의 캐릭터별 설정 칸: '옵션'과 '대사'.

두 칸 모두 같은 방식으로 다룹니다.
    load(values)    기본값 + character.json + 아직 적용 안 한 변경을 합친 값을 칸에 보여 줌
    changes(saved)  지금 칸 내용 중 character.json(saved)과 달라진 값만 돌려줌
"""
from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSpinBox, QVBoxLayout,
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

_DEFAULTS = PetConfig()


def _changed(values: Dict, saved: Dict) -> Dict:
    return {k: v for k, v in values.items() if saved.get(k, getattr(_DEFAULTS, k)) != v}


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
        self._frames: Dict[str, QSpinBox] = {}
        tick = _DEFAULTS.tick_ms
        for name, label in FRAME_OPTIONS:
            spin = QSpinBox()
            spin.setRange(tick, tick * 100)
            spin.setSingleStep(tick)
            spin.setSuffix(" ms")
            form.addRow(label + ":", spin)
            self._frames[name] = spin

    def load(self, values: Dict) -> None:
        self.faces_left.setChecked(bool(values["faces_left"]))
        self.max_size.setValue(int(values["max_size"]))
        for name, spin in self._frames.items():
            spin.setValue(int(values[name]) * _DEFAULTS.tick_ms)

    def changes(self, saved: Dict) -> Dict:
        values = {"faces_left": self.faces_left.isChecked(), "max_size": self.max_size.value()}
        for name, spin in self._frames.items():
            values[name] = max(1, round(spin.value() / _DEFAULTS.tick_ms))
        return _changed(values, saved)


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
        self.chance.setValue(round(float(values["idle_chat_chance"]) * 100))
        self._texts = {name: _shown_lines(values["lines"], name) for name, _ in LINE_SITUATIONS}
        self._fill_list()

    def changes(self, saved: Dict) -> Dict:
        changed = _changed({"idle_chat_chance": self.chance.value() / 100}, saved)
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
