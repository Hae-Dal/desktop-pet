"""업데이트 내역 창과 '새 버전으로 처음 실행했는지' 확인.

내용은 프로젝트 폴더의 CHANGELOG.md에서 릴리스된 버전 항목만 골라 보여 줍니다
(맨 위 안내·주석과 '미반영' 항목은 숨김).
마지막으로 실행한 버전은 prefs에 저장됩니다.
"""
import re
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from pet import __version__
from pet.config import BUNDLE_DIR
from pet.ui import prefs

CHANGELOG_PATH = Path(BUNDLE_DIR) / "CHANGELOG.md"


def is_new_version() -> bool:
    """이번 버전으로 처음 실행했으면 True. 확인한 버전은 바로 기록합니다."""
    if prefs.last_seen_version() == __version__:
        return False
    prefs.set_last_seen_version(__version__)
    return True


def released_notes(text: str) -> str:
    """'## 0.4.0 - 날짜' 같은 버전 항목만 남김."""
    sections = re.split(r"^(?=## )", text, flags=re.M)
    kept = [s.strip() for s in sections if re.match(r"## \d+\.\d+\.\d+", s)]
    return "\n\n".join(kept) or "아직 업데이트 내역이 없습니다."


class ChangelogDialog(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle(f"업데이트 내역 - v{__version__}")
        self.resize(480, 520)

        view = QTextBrowser(self)
        view.setOpenExternalLinks(True)
        try:
            text = released_notes(CHANGELOG_PATH.read_text(encoding="utf-8"))
        except OSError:
            text = "CHANGELOG.md를 찾을 수 없습니다."
        if hasattr(view, "setMarkdown"):      # Qt 5.14 이상
            view.setMarkdown(text)
        else:
            view.setPlainText(text)

        layout = QVBoxLayout(self)
        layout.addWidget(view)
