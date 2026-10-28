"""프로그램이 여러 번 실행되지 않게 막습니다.

잠금 파일(QLockFile)로 이미 실행 중인지 판단하고 (동시에 실행해도 하나만 통과,
비정상 종료로 남은 잠금은 자동 해제), 로컬 소켓으로 먼저 실행된 쪽에 알립니다.
"""
import getpass
import os

from PyQt5.QtCore import QLockFile, QObject, QStandardPaths, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

_KEY = f"desktop_pet-{getpass.getuser()}"     # 같은 PC의 다른 사용자와는 따로


class SingleInstance(QObject):
    activated = pyqtSignal()        # 다른 곳에서 또 실행하려고 했을 때

    def __init__(self):
        super().__init__()
        temp = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        self._lock = QLockFile(os.path.join(temp, _KEY + ".lock"))
        self._server = None

    def acquire(self) -> bool:
        """처음 실행이면 True. 이미 실행 중이면 그쪽에 알리고 False."""
        if not self._lock.tryLock(100):
            _notify_running()
            return False
        QLocalServer.removeServer(_KEY)           # 비정상 종료로 남은 소켓 정리 (macOS/Linux)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        self._server.listen(_KEY)
        return True

    def _on_connection(self) -> None:
        while self._server.hasPendingConnections():
            self._server.nextPendingConnection().deleteLater()
        self.activated.emit()


def _notify_running() -> None:
    socket = QLocalSocket()
    socket.connectToServer(_KEY)
    if socket.waitForConnected(500):
        socket.disconnectFromServer()
