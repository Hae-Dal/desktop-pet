"""우클릭 메뉴. 항목을 리스트로 등록하는 방식이라 추가·삭제가 쉽습니다."""
from dataclasses import dataclass
from typing import Callable, List

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QMenu, QWidget


@dataclass
class MenuItem:
    label: str
    callback: Callable[[], None]


def default_items(pet) -> List[MenuItem]:
    """펫 우클릭 메뉴. 항목을 늘리려면 여기에 MenuItem을 추가하세요."""
    items = [MenuItem("점프", pet.jump)]
    if pet.tray:                        # 숨기면 트레이 아이콘으로만 다시 부를 수 있으므로
        items.append(MenuItem("숨기기", pet.toggle_hidden))
    return items + _common_items(pet)


def tray_items(pet) -> List[MenuItem]:
    """트레이 아이콘 우클릭 메뉴."""
    return [MenuItem("보이기" if pet.is_hidden else "숨기기", pet.toggle_hidden)] + _common_items(pet)


def _common_items(pet) -> List[MenuItem]:
    items = [
        MenuItem("설정...", pet.show_settings),
        MenuItem("업데이트 내역", pet.show_changelog),
    ]
    if pet.updates.version:             # 새 버전이 있을 때만 보임
        items.append(MenuItem(f"새 버전 받기 (v{pet.updates.version})", pet.updates.open_page))
    items.append(MenuItem("종료", QApplication.quit))
    return items


def popup(parent: QWidget, items: List[MenuItem], pos: QPoint) -> None:
    menu = QMenu(parent)
    for item in items:
        action = menu.addAction(item.label)
        action.triggered.connect(item.callback)
    menu.exec_(pos)
