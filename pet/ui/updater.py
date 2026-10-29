"""새 버전 확인. GitHub Releases의 최신 버전과 비교해 더 새로우면 알립니다.

자동으로 내려받아 바꾸지는 않고, 알림과 릴리스 페이지 링크만 줍니다.
네트워크 오류·릴리스 없음(404)·이상한 응답은 모두 조용히 무시합니다.
"""
import json
import re
from typing import Optional, Tuple

from PyQt5.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from pet import __version__
from pet.ui import prefs

REPO = "Hae-Dal/desktop-pet"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
TIMEOUT_MS = 10000
START_DELAY_MS = 5000                       # 시작 말풍선과 겹치지 않게 조금 뒤에 첫 확인
INTERVAL_MS = 6 * 60 * 60 * 1000            # 켜 둔 동안 다시 확인하는 간격 (6시간)


def parse_version(text: str) -> Optional[Tuple[int, ...]]:
    """'v0.8.0' / '0.8.0' -> (0, 8, 0). 형식이 다르면 None."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    return tuple(int(n) for n in m.groups()) if m else None


class UpdateChecker(QObject):
    update_available = pyqtSignal(str, str)     # 새 버전 ("0.8.0"), 릴리스 페이지 주소

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._net = QNetworkAccessManager(self)

    def check(self) -> None:
        request = QNetworkRequest(QUrl(LATEST_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", f"desktop_pet/{__version__}".encode())
        if hasattr(request, "setTransferTimeout"):     # Qt 5.15 이상
            request.setTransferTimeout(TIMEOUT_MS)
        reply = self._net.get(request)
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply: QNetworkReply) -> None:
        reply.deleteLater()
        if reply.error() != QNetworkReply.NoError:
            return
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            latest = parse_version(data["tag_name"])
            url = data["html_url"]
        except (ValueError, KeyError, TypeError):
            return
        if latest and latest > parse_version(__version__):
            self.update_available.emit(".".join(map(str, latest)), url)


class UpdateWatcher(QObject):
    """켜 있는 동안 새 버전을 지켜봄: 시작 조금 뒤 한 번, 그 뒤로 INTERVAL_MS마다.

    설정에서 끄면 그 차례는 건너뛰고, 이미 알린 버전은 다시 알리지 않습니다.
    """
    found = pyqtSignal(str)                     # 처음 알게 된 새 버전 ("0.8.0")

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.version = ""                       # 알게 된 최신 버전 (없으면 "")
        self.url = ""                           # 그 버전의 릴리스 페이지
        self._checker = UpdateChecker(self)
        self._checker.update_available.connect(self._on_available)
        QTimer.singleShot(START_DELAY_MS, self._check)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._timer.start(INTERVAL_MS)

    def open_page(self) -> None:
        QDesktopServices.openUrl(QUrl(self.url))

    def _check(self) -> None:
        if prefs.check_updates():
            self._checker.check()

    def _on_available(self, version: str, url: str) -> None:
        if version == self.version:
            return
        self.version, self.url = version, url
        self.found.emit(version)
