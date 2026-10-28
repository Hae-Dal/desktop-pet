"""펫이 다른 창 뒤로 숨지 않게 '항상 위'를 주기적으로 다시 걸어 줍니다.

WindowStaysOnTopHint는 처음 한 번 '항상 위' 그룹에 넣어 줄 뿐이고, 그 그룹 안에서는
나중에 앞으로 나온 창(작업표시줄, 시작 메뉴, 알림, 다른 항상 위 프로그램)이 위에 옵니다.
"""
import sys

from PyQt5.QtWidgets import QApplication, QWidget

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _set_window_pos = ctypes.windll.user32.SetWindowPos
    # 인자 형식을 정하지 않으면 HWND_TOPMOST(-1)가 64비트 핸들로 제대로 넘어가지 않음
    _set_window_pos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    _HWND_TOPMOST = wintypes.HWND(-1)
    _FLAGS = 0x0001 | 0x0002 | 0x0010       # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE


def bring_to_front(*widgets: QWidget) -> None:
    """보이는 위젯을 순서대로 맨 앞으로 (나중 것이 더 위). 포커스는 뺏지 않음."""
    if QApplication.activePopupWidget():      # 우클릭 메뉴가 열려 있으면 가리지 않게 건너뜀
        return
    for widget in widgets:
        if not widget.isVisible():
            continue
        if sys.platform == "win32":
            _set_window_pos(int(widget.winId()), _HWND_TOPMOST, 0, 0, 0, 0, _FLAGS)
        else:
            widget.raise_()
