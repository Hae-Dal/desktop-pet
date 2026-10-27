"""업데이트 내역 창과 '새 버전으로 처음 실행했는지' 확인.

내용은 프로젝트 폴더의 CHANGELOG.md를 그대로 읽어 보여 주므로 따로 적을 곳이 없습니다.
마지막으로 실행한 버전은 QSettings에 저장됩니다 (Windows는 레지스트리, macOS/Linux는 설정 파일).
"""
from pathlib import Path

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from pet import __version__

CHANGELOG_PATH = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
_SEEN_KEY = "last_seen_version"


def is_new_version() -> bool:
    """이번 버전으로 처음 실행했으면 True. 확인한 버전은 바로 기록합니다."""
    settings = QSettings("desktop_pet", "desktop_pet")
    if settings.value(_SEEN_KEY) == __version__:
        return False
    settings.setValue(_SEEN_KEY, __version__)
    return True


class ChangelogDialog(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle(f"업데이트 내역 - v{__version__}")
        self.resize(480, 520)

        view = QTextBrowser(self)
        view.setOpenExternalLinks(True)
        try:
            text = CHANGELOG_PATH.read_text(encoding="utf-8")
        except OSError:
            text = "CHANGELOG.md를 찾을 수 없습니다."
        if hasattr(view, "setMarkdown"):      # Qt 5.14 이상
            view.setMarkdown(text)
        else:
            view.setPlainText(text)

        layout = QVBoxLayout(self)
        layout.addWidget(view)
