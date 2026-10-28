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
    """기본 메뉴 항목. 항목을 늘리려면 여기에 MenuItem을 추가하세요."""
    items = [
        MenuItem("점프", pet.jump),
        MenuItem("설정...", pet.show_settings),
        MenuItem("업데이트 내역", pet.show_changelog),
    ]
    if pet.new_version:                 # 새 버전이 있을 때만 보임
        items.append(MenuItem(f"새 버전 받기 (v{pet.new_version})", pet.open_update_page))
    items.append(MenuItem("종료", QApplication.quit))
    return items


def popup(parent: QWidget, items: List[MenuItem], pos: QPoint) -> None:
    menu = QMenu(parent)
    for item in items:
        action = menu.addAction(item.label)
        action.triggered.connect(item.callback)
    menu.exec_(pos)
