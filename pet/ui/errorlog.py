"""처리되지 않은 오류를 파일에 남기고 앱이 꺼지지 않게 합니다.

PyQt5는 타이머·마우스 이벤트 안에서 난 Python 오류를 처리하지 않으면 앱을 바로 종료하고
아무 기록도 남기지 않습니다. sys.excepthook을 바꾸면 종료 대신 이 훅이 호출됩니다.
Qt 내부에서 죽는 경우는 faulthandler가 마지막 위치를 같은 파일에 남깁니다.

로그 위치 (QStandardPaths.AppDataLocation):
    Windows  %APPDATA%/desktop_pet/desktop_pet/error.log
    macOS    ~/Library/Application Support/desktop_pet/desktop_pet/error.log
    Linux    ~/.local/share/desktop_pet/desktop_pet/error.log
"""
import datetime
import faulthandler
import sys
import traceback
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

from pet import __version__

_seen = set()        # 같은 오류가 매 tick 반복돼도 한 번만 기록
_fault_file = None   # faulthandler가 쓰는 파일은 열린 채로 유지해야 함


def log_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return Path(base) / "error.log"


def install() -> Path:
    """QApplication 생성 직후, 이름을 정한 다음에 호출."""
    global _fault_file
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    _fault_file = open(path, "a", encoding="utf-8")
    faulthandler.enable(_fault_file)
    sys.excepthook = _hook
    return path


def _hook(exc_type, exc, tb) -> None:
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    if sys.__stderr__:                  # pythonw로 실행하면 None
        sys.__stderr__.write(text)
    if text in _seen:
        return
    _seen.add(text)
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    _fault_file.write(f"\n[{stamp}] v{__version__}\n{text}")
    _fault_file.flush()
