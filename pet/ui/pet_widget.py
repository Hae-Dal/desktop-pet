"""펫 창: 창 설정, 그리기, 마우스 입력. 행동 판단은 pet/core/states가 합니다.

새 버전 확인은 updater, 이스터에그 판정은 easter_egg, 항상 위 유지는 topmost에 있습니다.
"""
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QDialog, QWidget

from pet import __version__
from pet.config import PetConfig
from pet.core.context import PetContext
from pet.core.states import StateMachine, TimedState, build_states
from pet.ui import changelog, easter_egg, menu, topmost, updater
from pet.ui.bubble import BubbleWidget
from pet.ui.settings_dialog import SettingsDialog
from pet.ui.sprites import SpriteSet
from pet.ui.world import World

KEEP_IN_FRONT_MS = 1000


class PetWidget(QWidget):
    def __init__(self, config: PetConfig, sprites: SpriteSet, world: World):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.ctx = PetContext(config, world, *sprites.size)
        self.bubble = BubbleWidget()
        self._load(config, sprites)
        self.ctx.x = world.random_x(self.ctx.width)
        self.ctx.snap_to_ground()
        self.move(self.ctx.x, self.ctx.y)
        self.machine.change("idle")

        self._changelog = None
        self._settings = None

        self.updates = updater.UpdateWatcher(self)  # 새 버전이 있으면 우클릭 메뉴에 받기 항목이 생김
        self.updates.found.connect(
            lambda v: self.ctx.say(f"새 버전 v{v}이 나왔어!\n우클릭 → 새 버전 받기", 200))
        if changelog.is_new_version():
            self.ctx.say(f"v{__version__}로 업데이트됐어!\n우클릭 → 업데이트 내역", 150)

        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._moved = False
        self._clicks = easter_egg.RapidClicks(config.easter_egg_clicks, config.easter_egg_seconds)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(config.tick_ms)

        self._front_timer = QTimer(self)                # 다른 창 뒤로 숨지 않게
        self._front_timer.timeout.connect(lambda: topmost.bring_to_front(self, self.bubble))
        self._front_timer.start(KEEP_IN_FRONT_MS)

    def _load(self, config: PetConfig, sprites: SpriteSet) -> None:
        """설정과 이미지를 적용하고 상태들을 새로 만듦 (상태들이 설정값을 미리 읽어 두므로)."""
        self.config, self.sprites = config, sprites
        self.ctx.config = config
        self.ctx.width, self.ctx.height = sprites.size
        self.resize(*sprites.size)
        self.machine = StateMachine(build_states(self.ctx))

    # ---------- 루프 ----------
    def _tick(self) -> None:
        self.machine.update()
        self.ctx.tick_bubble()
        self.move(self.ctx.x, self.ctx.y)
        self._sync_bubble()
        self.update()

    def _sync_bubble(self) -> None:
        text = self.ctx.bubble_text
        if not text:
            self.bubble.hide()
            return
        self.bubble.set_text(text)
        c = self.ctx
        self.bubble.follow(self.frameGeometry(), c.world.area_at(c.x, c.y, c.width, c.height))
        if not self.bubble.isVisible():
            self.bubble.show()

    # ---------- 동작 ----------
    def jump(self) -> None:
        """바닥에서 하는 행동 중이면 점프 (공중이거나 잡혀 있으면 무시)."""
        if isinstance(self.machine.current, TimedState) and self.ctx.on_ground:
            self.machine.change("jump")

    def greet(self) -> None:
        """프로그램을 또 실행하려고 했을 때: 이미 여기 있다고 알림."""
        self.jump()                                  # 자는 중이면 깨면서 말풍선이 지워지므로 먼저
        self.ctx.say("나 이미 여기 있어!", 90)

    def change_character(self, name: str) -> None:
        """설정 창에서 적용: 이미지와 캐릭터별 설정을 다시 읽어 바로 바꿈."""
        config = PetConfig(character=name, sprites_root=self.config.sprites_root).with_character_settings()
        self._load(config, SpriteSet.load(config))
        self.machine.change("fall")                  # 크기가 바뀌었을 수 있으니 바닥으로
        self.update()

    def show_settings(self) -> None:
        if self._settings is None or not self._settings.isVisible():
            self._settings = SettingsDialog(self.config.sprites_root, self.config.character,
                                            self.change_character)
        _bring_up(self._settings)

    def show_changelog(self) -> None:
        if self._changelog is None:
            self._changelog = changelog.ChangelogDialog()
        _bring_up(self._changelog)

    # ---------- 그리기 ----------
    def paintEvent(self, _) -> None:
        pix = self.sprites.frame(self.ctx.animation, self.ctx.frame_idx, self.ctx.facing)
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap((self.width() - pix.width()) // 2, self.height() - pix.height(), pix)

    # ---------- 마우스 ----------
    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton:
            self._moved = False
            self._press_pos = e.globalPos()
            self._drag_offset = e.globalPos() - self.frameGeometry().topLeft()
            was_sleeping = self.machine.current_name == "sleep"
            self.machine.change("drag")
            if was_sleeping:
                self.ctx.say("으앗! 깜짝이야", 60)
        elif e.button() == Qt.RightButton:
            menu.popup(self, menu.default_items(self), e.globalPos())

    def mouseMoveEvent(self, e) -> None:
        if self.machine.current_name == "drag" and e.buttons() & Qt.LeftButton:
            if not self._moved:             # 손떨림 정도는 클릭으로 취급
                if (e.globalPos() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
                    return
                self._moved = True
            pos = e.globalPos() - self._drag_offset
            self.ctx.x, self.ctx.y = pos.x(), pos.y()
            self.move(pos)

    def mouseReleaseEvent(self, e) -> None:
        if e.button() != Qt.LeftButton or self.machine.current_name != "drag":
            return
        clicked = not self._moved
        # 그냥 클릭 = 점프, 끌어서 놓으면 중력으로 떨어짐
        self.machine.change("jump" if clicked and self.ctx.on_ground else "fall")
        if clicked and self._clicks.click():
            self._find_easter_egg()

    def _find_easter_egg(self) -> None:
        if self.config.character == easter_egg.NAME or not easter_egg.available(self.config.sprites_root):
            return                                   # 이미 그 캐릭터거나, 이미지가 없는 PC
        easter_egg.reveal(self.config.sprites_root)
        self.change_character(easter_egg.NAME)
        self.ctx.say("짠! 물범이랑 같이 왔어", 120)


def _bring_up(dialog: QDialog) -> None:
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
