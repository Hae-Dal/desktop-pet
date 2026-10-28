"""설정 창: 왼쪽 캐릭터 목록, 오른쪽 그 캐릭터의 이미지·옵션, 아래 일반 설정.

바꾼 내용은 [적용]/[확인]을 누를 때 한꺼번에 파일에 쓰고, [취소]하면 버립니다.
(캐릭터 새로 만들기·삭제만 누르는 즉시 반영)
각 칸은 images.py, options.py에 있습니다.
"""
import os
from dataclasses import asdict
from typing import Callable, Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QInputDialog, QListWidget,
    QMessageBox, QPushButton, QVBoxLayout,
)

from pet.config import PetConfig
from pet.ui import characters, prefs
from pet.ui.settings.images import ImagePanel
from pet.ui.settings.options import LinesPanel, OptionsPanel


class SettingsDialog(QDialog):
    def __init__(self, sprites_root: str, current: str, on_apply: Callable[[str], None]):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle("설정")
        self.root = sprites_root
        self.on_apply = on_apply

        self._options: Dict[str, Dict] = {}      # 캐릭터 -> 아직 적용 안 한 character.json 변경
        self._shown: Optional[str] = None        # 지금 오른쪽에 보이는 캐릭터

        # --- 캐릭터 목록 ---
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

        # --- 캐릭터별 칸 ---
        self.images = ImagePanel()
        self.options = OptionsPanel()
        self.lines = LinesPanel()
        self._panels = [self.options, self.lines]   # load/changes로 다루는 칸

        # --- 일반 (캐릭터와 상관없는 설정) ---
        general_box = QGroupBox("일반")
        general = QVBoxLayout(general_box)
        self.check_updates = QCheckBox("새 버전이 나오면 알려 주기")
        self.check_updates.setChecked(prefs.check_updates())
        general.addWidget(self.check_updates)

        left = QVBoxLayout()
        left.addWidget(char_box, 1)
        left.addWidget(self.lines, 1)
        right = QVBoxLayout()
        right.addWidget(self.images)
        right.addWidget(self.options)
        right.addWidget(general_box)
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
    def _char_dir(self, name: str) -> str:
        return os.path.join(self.root, name)

    def _reload_list(self, select: Optional[str]) -> None:
        names = characters.list_characters(self.root)
        self._shown = None
        self.list.clear()
        self.list.addItems(names)
        if names:
            self.list.setCurrentRow(names.index(select) if select in names else 0)
        else:
            self._show_character("")

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
        self._remember_changes()
        characters.create_character(self.root, name)
        self._reload_list(name)

    def _delete_character(self) -> None:
        name = self.list.currentItem().text()
        answer = QMessageBox.question(
            self, "캐릭터 삭제", f"'{name}' 캐릭터와 폴더 안의 이미지를 모두 지울까요?\n되돌릴 수 없습니다.")
        if answer != QMessageBox.Yes:
            return
        characters.delete_character(self.root, name)
        self.images.forget(self._char_dir(name))
        self._options.pop(name, None)
        self._reload_list(None)

    # ---------- 캐릭터별 칸 ----------
    def _show_character(self, name: str) -> None:
        self._remember_changes()
        self._shown = name or None
        self.delete_btn.setEnabled(bool(name))
        self.images.show_character(self._char_dir(name) if name else None)
        for panel in self._panels:
            panel.setEnabled(bool(name))
        if not name:
            self.lines.list.clear()
            return
        values = asdict(PetConfig())
        values.update(characters.read_settings(self._char_dir(name)))
        values.update(self._options.get(name, {}))
        for panel in self._panels:
            panel.load(values)

    def _remember_changes(self) -> None:
        """보이던 캐릭터의 칸 내용 중 바뀐 것을 기억 (다른 캐릭터로 넘어가거나 적용하기 전에 호출)."""
        if not self._shown:
            return
        saved = characters.read_settings(self._char_dir(self._shown))
        changed = {}
        for panel in self._panels:
            changed.update(panel.changes(saved))
        if changed:
            self._options[self._shown] = changed
        else:
            self._options.pop(self._shown, None)

    # ---------- 확인 / 적용 ----------
    def _apply(self) -> None:
        self._remember_changes()
        self.images.apply()
        for name, values in self._options.items():
            characters.write_settings(self._char_dir(name), values)
        self._options.clear()
        prefs.set_check_updates(self.check_updates.isChecked())
        if self._shown:
            prefs.set_active_character(self._shown)
            self.on_apply(self._shown)

    def _ok(self) -> None:
        self._apply()
        self.accept()

    def done(self, result: int) -> None:
        self.images.stop()
        super().done(result)
