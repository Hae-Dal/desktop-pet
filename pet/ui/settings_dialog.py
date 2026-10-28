"""설정 창: 캐릭터 고르기, 동작별 이미지 넣기, 캐릭터별 옵션과 대사.

바꾼 내용은 [적용]/[확인]을 누를 때 한꺼번에 파일에 쓰고, [취소]하면 버립니다.
(캐릭터 새로 만들기·삭제만 누르는 즉시 반영)
"""
import os
from dataclasses import fields
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import QBuffer, QByteArray, QSize, Qt
from PyQt5.QtGui import QImageReader, QMovie, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSpinBox, QVBoxLayout,
)

from pet.config import DEFAULT_LINES, PetConfig
from pet.ui import characters, updater

PREVIEW = 64           # 미리보기 칸 크기(px)
IMAGE_FILTER = "이미지 (*.png *.gif)"

# 옵션 칸: (설정 이름, 표시 이름). 프레임 간격은 tick 단위로 저장하고 ms로 보여 줌
FRAME_OPTIONS = [
    ("frame_every", "기본 프레임 간격"),
    ("walk_frame_every", "걷기 프레임 간격"),
    ("sleep_frame_every", "잠자기 프레임 간격"),
]

# 대사 칸에서 고칠 수 있는 상황. 나중에 상황을 늘리면 고를 수 있게 하면 됨
LINE_SITUATION = "idle"


class SettingsDialog(QDialog):
    def __init__(self, sprites_root: str, current: str, on_apply: Callable[[str], None]):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle("설정")
        self.root = sprites_root
        self.on_apply = on_apply
        self.defaults = PetConfig()

        self._files: Dict[str, Dict[str, Optional[str]]] = {}   # 캐릭터 -> 동작 -> 새 파일 (None이면 지움)
        self._options: Dict[str, Dict] = {}                      # 캐릭터 -> 바꾼 옵션
        self._shown: Optional[str] = None                        # 지금 오른쪽에 보이는 캐릭터
        self._movies = []

        # --- 캐릭터 ---
        self.list = QListWidget()
        self.list.currentTextChanged.connect(self._show_character)
        new_btn = QPushButton("새로 만들기...")
        new_btn.clicked.connect(self._new_character)
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self._delete_character)
        char_buttons = QHBoxLayout()
        char_buttons.addWidget(new_btn)
        char_buttons.addWidget(self.delete_btn)
        char_box = QGroupBox("캐릭터")
        char_layout = QVBoxLayout(char_box)
        char_layout.addWidget(self.list)
        char_layout.addLayout(char_buttons)

        # --- 대사 (혼잣말) ---
        lines_box = QGroupBox("혼잣말")
        lines_layout = QVBoxLayout(lines_box)
        self.lines = QListWidget()
        add_line = QPushButton("추가")
        add_line.clicked.connect(self._add_line)
        self.remove_line = QPushButton("삭제")
        self.remove_line.clicked.connect(self._remove_line)
        line_buttons = QHBoxLayout()
        line_buttons.addWidget(add_line)
        line_buttons.addWidget(self.remove_line)
        self.chat_chance = QSpinBox()
        self.chat_chance.setRange(0, 100)
        self.chat_chance.setSuffix(" %")
        chance_row = QFormLayout()
        chance_row.addRow("말할 확률:", self.chat_chance)
        lines_note = QLabel("두 번 클릭하면 고칠 수 있어요.\n모두 지우면 기본 대사로 돌아갑니다.")
        lines_note.setEnabled(False)
        lines_layout.addWidget(self.lines)
        lines_layout.addLayout(line_buttons)
        lines_layout.addLayout(chance_row)
        lines_layout.addWidget(lines_note)
        self._line_widgets = [self.lines, add_line, self.remove_line, self.chat_chance]

        # --- 이미지 ---
        image_box = QGroupBox("이미지")
        grid = QGridLayout(image_box)
        self._previews: Dict[str, QLabel] = {}
        for row, (anim, label) in enumerate(characters.ANIMATIONS):
            preview = QLabel()
            preview.setFixedSize(PREVIEW, PREVIEW)
            preview.setAlignment(Qt.AlignCenter)
            preview.setFrameShape(QFrame.StyledPanel)
            preview.setFrameShadow(QFrame.Sunken)
            browse = QPushButton("찾아보기...")
            browse.clicked.connect(lambda _, a=anim: self._browse(a))
            clear = QPushButton("지우기")
            clear.clicked.connect(lambda _, a=anim: self._clear(a))
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(preview, row, 1)
            grid.addWidget(browse, row, 2)
            grid.addWidget(clear, row, 3)
            self._previews[anim] = preview
        note = QLabel("이미지가 없는 동작은 '가만히 있기' 이미지로 대신합니다.")
        note.setEnabled(False)
        grid.addWidget(note, len(characters.ANIMATIONS), 0, 1, 4)

        # --- 옵션 ---
        option_box = QGroupBox("옵션")
        form = QFormLayout(option_box)
        self.faces_left = QCheckBox("이미지 속 캐릭터가 왼쪽을 봄")
        form.addRow(self.faces_left)
        self.max_size = QSpinBox()
        self.max_size.setRange(16, 1024)
        self.max_size.setSuffix(" px")
        form.addRow("최대 크기:", self.max_size)
        self._frame_spins: Dict[str, QSpinBox] = {}
        tick = self.defaults.tick_ms
        for name, label in FRAME_OPTIONS:
            spin = QSpinBox()
            spin.setRange(tick, tick * 100)
            spin.setSingleStep(tick)
            spin.setSuffix(" ms")
            form.addRow(label + ":", spin)
            self._frame_spins[name] = spin

        # --- 일반 (캐릭터와 상관없는 설정) ---
        general_box = QGroupBox("일반")
        general = QVBoxLayout(general_box)
        self.check_updates = QCheckBox("새 버전이 나오면 알려 주기")
        self.check_updates.setChecked(updater.is_enabled())
        general.addWidget(self.check_updates)

        right = QVBoxLayout()
        right.addWidget(image_box)
        right.addWidget(option_box)
        right.addWidget(general_box)
        left = QVBoxLayout()
        left.addWidget(char_box, 1)
        left.addWidget(lines_box, 1)
        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 2)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.button(QDialogButtonBox.Ok).setText("확인")
        buttons.button(QDialogButtonBox.Cancel).setText("취소")
        buttons.button(QDialogButtonBox.Apply).setText("적용")
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply)

        layout = QVBoxLayout(self)
        layout.addLayout(body)
        layout.addWidget(buttons)

        self._reload_list(current)

    # ---------- 캐릭터 목록 ----------
    def _reload_list(self, select: Optional[str]) -> None:
        names = characters.list_characters(self.root)
        self._shown = None
        self.list.clear()
        self.list.addItems(names)
        if names:
            self.list.setCurrentRow(names.index(select) if select in names else 0)
        else:
            self._show_character("")

    def _char_dir(self, name: str) -> str:
        return os.path.join(self.root, name)

    def _new_character(self) -> None:
        name, ok = QInputDialog.getText(self, "새 캐릭터", "캐릭터 이름 (폴더 이름으로 쓰입니다):")
        if not ok:
            return
        name = name.strip()
        if not characters.is_valid_name(name):
            QMessageBox.warning(self, "새 캐릭터", '이름에 \\ / : * ? " < > | 는 쓸 수 없습니다.')
            return
        if characters.exists(self.root, name):
            QMessageBox.warning(self, "새 캐릭터", f"'{name}' 캐릭터가 이미 있습니다.")
            return
        self._store_options()
        characters.create_character(self.root, name)
        self._reload_list(name)

    def _delete_character(self) -> None:
        name = self.list.currentItem().text()
        answer = QMessageBox.question(
            self, "캐릭터 삭제", f"'{name}' 캐릭터와 폴더 안의 이미지를 모두 지울까요?\n되돌릴 수 없습니다.")
        if answer != QMessageBox.Yes:
            return
        characters.delete_character(self.root, name)
        self._files.pop(name, None)
        self._options.pop(name, None)
        self._reload_list(None)

    # ---------- 오른쪽 칸 ----------
    def _show_character(self, name: str) -> None:
        self._store_options()
        self._shown = name or None
        self.delete_btn.setEnabled(bool(name))
        for w in [self.faces_left, self.max_size, *self._frame_spins.values(), *self._line_widgets]:
            w.setEnabled(bool(name))
        if not name:
            for anim, _ in characters.ANIMATIONS:
                self._set_preview(anim, None)
            self.lines.clear()
            return

        for anim, _ in characters.ANIMATIONS:
            self._set_preview(anim, self._effective_file(name, anim))

        values = {f.name: getattr(self.defaults, f.name) for f in fields(self.defaults)}
        values.update(characters.read_settings(self._char_dir(name)))
        values.update(self._options.get(name, {}))
        self.faces_left.setChecked(bool(values["faces_left"]))
        self.max_size.setValue(int(values["max_size"]))
        for opt, spin in self._frame_spins.items():
            spin.setValue(int(values[opt]) * self.defaults.tick_ms)
        self.chat_chance.setValue(round(float(values["idle_chat_chance"]) * 100))
        lines = (self._options.get(name, {}).get("lines")
                 or _saved_lines(characters.read_settings(self._char_dir(name))))
        self._set_lines(lines.get(LINE_SITUATION) or DEFAULT_LINES[LINE_SITUATION])

    def _store_options(self) -> None:
        """보이던 캐릭터의 옵션 칸 값을 기억 (목록을 바꾸거나 적용하기 전에 호출)."""
        if not self._shown:
            return
        tick = self.defaults.tick_ms
        values = {"faces_left": self.faces_left.isChecked(), "max_size": self.max_size.value()}
        for opt, spin in self._frame_spins.items():
            values[opt] = max(1, round(spin.value() / tick))
        values["idle_chat_chance"] = self.chat_chance.value() / 100
        saved = characters.read_settings(self._char_dir(self._shown))
        changed = {k: v for k, v in values.items()
                   if saved.get(k, getattr(self.defaults, k)) != v}
        saved_lines = _saved_lines(saved)
        edited = self._edited_lines()
        if edited != list(saved_lines.get(LINE_SITUATION) or DEFAULT_LINES[LINE_SITUATION]):
            changed["lines"] = {**saved_lines, LINE_SITUATION: edited}   # 다른 상황 대사는 그대로 둠
        if changed:
            self._options[self._shown] = changed
        else:
            self._options.pop(self._shown, None)

    # ---------- 대사 ----------
    def _set_lines(self, lines) -> None:
        self.lines.clear()
        for text in lines:
            self._append_line(text)

    def _append_line(self, text: str) -> QListWidgetItem:
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.lines.addItem(item)
        return item

    def _edited_lines(self) -> List[str]:
        """대사 칸 내용 (빈 줄은 뺌). 비어 있으면 기본 대사를 쓰라는 뜻."""
        texts = (self.lines.item(i).text().strip() for i in range(self.lines.count()))
        return [t for t in texts if t]

    def _add_line(self) -> None:
        item = self._append_line("")
        self.lines.setCurrentItem(item)
        self.lines.editItem(item)

    def _remove_line(self) -> None:
        row = self.lines.currentRow()
        if row >= 0:
            self.lines.takeItem(row)

    def _effective_file(self, name: str, anim: str) -> Optional[str]:
        pending = self._files.get(name, {})
        if anim in pending:
            return pending[anim]
        return characters.animation_file(self._char_dir(name), anim)

    def _set_preview(self, anim: str, path: Optional[str]) -> None:
        label = self._previews[anim]
        old = label.movie()
        if old:
            old.stop()
            self._movies.remove(old)
        label.setMovie(None)
        label.clear()
        if not path:
            label.setText("없음")
            return
        if path.lower().endswith(".gif"):
            # 파일을 열어 둔 채로 두면 Windows에서 적용할 때 지우거나 덮어쓸 수 없어 메모리로 읽음
            with open(path, "rb") as f:
                buffer = QBuffer(self)
                buffer.setData(QByteArray(f.read()))
            movie = QMovie(buffer, QByteArray(), buffer)
            movie.jumpToFrame(0)
            movie.setScaledSize(_fit(movie.currentImage().size()))
            label.setMovie(movie)
            self._movies.append(movie)       # 참조를 잡아 두지 않으면 바로 사라짐
            movie.start()
        else:
            pix = QPixmap(path)
            label.setPixmap(pix.scaled(_fit(pix.size()), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _browse(self, anim: str) -> None:
        if not self._shown:
            return
        path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", IMAGE_FILTER)
        if not path:
            return
        if QImageReader(path).read().isNull():
            QMessageBox.warning(self, "이미지 선택", "이미지를 읽을 수 없습니다.")
            return
        self._files.setdefault(self._shown, {})[anim] = path
        self._set_preview(anim, path)

    def _clear(self, anim: str) -> None:
        if not self._shown:
            return
        self._files.setdefault(self._shown, {})[anim] = None
        self._set_preview(anim, None)

    # ---------- 확인 / 적용 ----------
    def _apply(self) -> None:
        self._store_options()
        for name, anims in self._files.items():
            for anim, src in anims.items():
                if src:
                    characters.set_animation(self._char_dir(name), anim, src)
                else:
                    characters.clear_animation(self._char_dir(name), anim)
        for name, values in self._options.items():
            # 예전 형식 혼잣말 목록은 새 형식(lines)으로 옮겨 저장하니 지움
            characters.write_settings(self._char_dir(name), values,
                                      remove=["idle_lines"] if "lines" in values else [])
        self._files.clear()
        self._options.clear()
        updater.set_enabled(self.check_updates.isChecked())
        if self._shown:
            characters.set_active_character(self._shown)
            self.on_apply(self._shown)

    def _ok(self) -> None:
        self._apply()
        self.accept()

    def done(self, result: int) -> None:
        for movie in self._movies:
            movie.stop()
        super().done(result)


def _saved_lines(saved: Dict) -> Dict[str, List[str]]:
    """character.json의 상황별 대사 (예전 형식 혼잣말 목록도 읽음)."""
    lines = dict(saved.get("lines", {}))
    if "idle_lines" in saved:
        lines.setdefault("idle", saved["idle_lines"])
    return lines


def _fit(size: QSize) -> QSize:
    """미리보기 칸에 들어가게 비율 유지 축소 (작은 이미지는 그대로)."""
    if size.width() <= PREVIEW and size.height() <= PREVIEW:
        return size
    return size.scaled(PREVIEW, PREVIEW, Qt.KeepAspectRatio)
