"""설정 창의 캐릭터별 설정 칸: '옵션'과 '혼잣말'.

두 칸 모두 같은 방식으로 다룹니다.
    load(values)    기본값 + character.json + 아직 적용 안 한 변경을 합친 값을 칸에 보여 줌
    changes(saved)  지금 칸 내용 중 character.json(saved)과 달라진 값만 돌려줌
"""
from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSpinBox, QVBoxLayout,
)

from pet.config import DEFAULT_LINES, PetConfig

# 프레임 간격: (설정 이름, 표시 이름). tick 단위로 저장하고 ms로 보여 줌
FRAME_OPTIONS = [
    ("frame_every", "기본 프레임 간격"),
    ("walk_frame_every", "걷기 프레임 간격"),
    ("sleep_frame_every", "잠자기 프레임 간격"),
]

# 혼잣말 칸에서 고칠 수 있는 상황. 나중에 상황을 늘리면 고를 수 있게 하면 됨
LINE_SITUATION = "idle"

_DEFAULTS = PetConfig()


def _changed(values: Dict, saved: Dict) -> Dict:
    return {k: v for k, v in values.items() if saved.get(k, getattr(_DEFAULTS, k)) != v}


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
        super().__init__("혼잣말")
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
        note = QLabel("두 번 클릭하면 고칠 수 있어요.\n모두 지우면 기본 대사로 돌아갑니다.")
        note.setEnabled(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(buttons)
        layout.addLayout(chance_row)
        layout.addWidget(note)

    def load(self, values: Dict) -> None:
        self.chance.setValue(round(float(values["idle_chat_chance"]) * 100))
        self.list.clear()
        for text in values["lines"].get(LINE_SITUATION) or DEFAULT_LINES[LINE_SITUATION]:
            self._append(text)

    def changes(self, saved: Dict) -> Dict:
        changed = _changed({"idle_chat_chance": self.chance.value() / 100}, saved)
        saved_lines = saved.get("lines", {})
        edited = self.texts()
        if edited != list(saved_lines.get(LINE_SITUATION) or DEFAULT_LINES[LINE_SITUATION]):
            changed["lines"] = {**saved_lines, LINE_SITUATION: edited}   # 다른 상황 대사는 그대로 둠
        return changed

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
