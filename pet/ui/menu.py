"""우클릭 메뉴. 항목을 리스트로 등록하는 방식이라 추가·삭제가 쉽습니다."""
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QMenu, QWidget

# 크기 메뉴: (표시 이름, 배율)
SIZES = [("작게", 0.75), ("보통", 1.0), ("크게", 1.5), ("아주 크게", 2.0)]
# 조용히 하기 메뉴: (표시 이름, 초)
QUIET_TIMES = [("30분", 30 * 60), ("1시간", 60 * 60), ("3시간", 3 * 60 * 60)]


@dataclass
class MenuItem:
    label: str
    callback: Optional[Callable[[], None]] = None
    checked: Optional[bool] = None                          # None이 아니면 체크 표시가 있는 항목
    children: List["MenuItem"] = field(default_factory=list)  # 있으면 하위 메뉴


def default_items(pet) -> List[MenuItem]:
    """펫 우클릭 메뉴. 항목을 늘리려면 여기에 MenuItem을 추가하세요."""
    items = [MenuItem("점프", pet.jump)]
    if pet.tray:                        # 숨기면 트레이 아이콘으로만 다시 부를 수 있으므로
        items.append(MenuItem("숨기기", pet.toggle_hidden))
    return items + _pet_items(pet) + _common_items(pet)


def tray_items(pet) -> List[MenuItem]:
    """트레이 아이콘 우클릭 메뉴."""
    hide = MenuItem("보이기" if pet.is_hidden else "숨기기", pet.toggle_hidden)
    return [hide] + _pet_items(pet) + _common_items(pet)


def _pet_items(pet) -> List[MenuItem]:
    sizes = [MenuItem(label, lambda s=scale: pet.set_scale(s), checked=pet.scale == scale)
             for label, scale in SIZES]
    left = pet.ctx.quiet_seconds_left
    if left:
        quiet = MenuItem(f"조용히 하는 중 ({_minutes(left)}분 남음)",
                         children=[MenuItem("다시 말하기", lambda: pet.ctx.be_quiet(0))])
    else:
        quiet = MenuItem("조용히 하기", children=[
            MenuItem(label, lambda s=seconds: pet.ctx.be_quiet(s)) for label, seconds in QUIET_TIMES])
    return [MenuItem("크기", children=sizes), quiet]


def _minutes(seconds: float) -> int:
    return max(1, round(seconds / 60))


def _common_items(pet) -> List[MenuItem]:
    items = [
        MenuItem("설정...", pet.show_settings),
        MenuItem("업데이트 내역", pet.show_changelog),
    ]
    if pet.updates.version:             # 새 버전이 있을 때만 보임
        items.append(MenuItem(f"새 버전 받기 (v{pet.updates.version})", pet.updates.open_page))
    items.append(MenuItem("종료", QApplication.quit))
    return items


def fill(menu: QMenu, items: List[MenuItem]) -> None:
    """QMenu에 항목을 넣음 (하위 메뉴 포함)."""
    for item in items:
        if item.children:
            fill(menu.addMenu(item.label), item.children)
            continue
        action = menu.addAction(item.label)
        if item.checked is not None:
            action.setCheckable(True)
            action.setChecked(item.checked)
        if item.callback:
            action.triggered.connect(item.callback)


def popup(parent: QWidget, items: List[MenuItem], pos: QPoint) -> None:
    menu = QMenu(parent)
    fill(menu, items)
    menu.exec_(pos)
