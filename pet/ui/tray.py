"""작업 표시줄 알림 영역(트레이)의 펫 아이콘.

아이콘을 클릭하면 펫을 숨기거나 다시 보이고, 우클릭하면 메뉴가 나옵니다.
펫을 숨겨 둔 동안에는 여기서만 다시 불러올 수 있으므로, 트레이를 쓸 수 없는 환경에서는 숨기기 메뉴를 보이지 않습니다.
"""
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QSystemTrayIcon

from pet.ui import menu


def available() -> bool:
    return QSystemTrayIcon.isSystemTrayAvailable()


class Tray(QSystemTrayIcon):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.setToolTip("데스크톱 펫")
        self._menu = QMenu()
        self._menu.aboutToShow.connect(self._fill_menu)     # 열 때마다 새로 (숨김 상태·새 버전 반영)
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)
        self.update_icon()

    def update_icon(self) -> None:
        """펫의 가만히 있는 모습을 아이콘으로 (캐릭터를 바꾸면 다시 부름)."""
        self.setIcon(QIcon(self.pet.sprites.frame("idle", 0, 1)))

    def _fill_menu(self) -> None:
        self._menu.clear()
        for item in menu.tray_items(self.pet):
            self._menu.addAction(item.label).triggered.connect(item.callback)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:               # 왼쪽 클릭
            self.pet.toggle_hidden()
