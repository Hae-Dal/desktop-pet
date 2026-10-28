"""창 설정, 그리기, 마우스 입력만 담당합니다. 행동 판단은 pet/core/states가 합니다."""
import time

from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QWidget

from pet import __version__
from pet.config import PetConfig
from pet.core.context import PetContext
from pet.core.states import StateMachine, TimedState, build_states
from pet.ui import changelog, characters, menu
from pet.ui.bubble import BubbleWidget
from pet.ui.settings_dialog import SettingsDialog
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


class PetWidget(QWidget):
    def __init__(self, config: PetConfig, sprites: SpriteSet, world: World):
        super().__init__()
        self.config = config
        self.sprites = sprites

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(*sprites.size)

        self.ctx = PetContext(config, world, *sprites.size)
        self.ctx.x = world.random_x(self.ctx.width)
        self.ctx.snap_to_ground()
        self.move(self.ctx.x, self.ctx.y)

        self.machine = StateMachine(build_states(self.ctx))
        self.machine.change("idle")

        self.bubble = BubbleWidget()
        self._changelog = None
        self._settings = None
        if changelog.is_new_version():
            self.ctx.say(f"v{__version__}로 업데이트됐어!\n우클릭 → 업데이트 내역", 150)

        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._moved = False
        self._clicks = []                   # 최근 클릭 시각 (이스터에그 연타 판정)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(config.tick_ms)

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
        if isinstance(self.machine.current, TimedState) and self.ctx.on_ground:
            self.ctx.vy = self.config.jump_power
            self.machine.change("fall")

    def greet(self) -> None:
        """프로그램을 또 실행하려고 했을 때: 이미 여기 있다고 알림."""
        self.jump()                                  # 자는 중이면 깨면서 말풍선이 지워지므로 먼저
        self.ctx.say("나 이미 여기 있어!", 90)

    def show_settings(self) -> None:
        if self._settings is None or not self._settings.isVisible():
            self._settings = SettingsDialog(self.config.sprites_root, self.config.character,
                                            self.change_character)
        self._settings.show()
        self._settings.raise_()
        self._settings.activateWindow()

    def change_character(self, name: str) -> None:
        """설정 창에서 적용: 이미지와 캐릭터별 설정을 다시 읽어 바로 바꿈."""
        config = PetConfig(character=name).with_character_settings()
        self.config = config
        self.sprites = SpriteSet.load(config)
        self.ctx.config = config
        self.ctx.width, self.ctx.height = self.sprites.size
        self.resize(*self.sprites.size)
        self.machine = StateMachine(build_states(self.ctx))    # 상태들이 설정값을 미리 읽어 두므로 새로 만듦
        self.machine.change("fall")                            # 크기가 바뀌었으니 바닥으로
        self.update()

    def show_changelog(self) -> None:
        if self._changelog is None:
            self._changelog = changelog.ChangelogDialog()
        self._changelog.show()
        self._changelog.raise_()
        self._changelog.activateWindow()

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
        if e.button() == Qt.LeftButton and self.machine.current_name == "drag":
            if not self._moved and self.ctx.on_ground:
                self.ctx.vy = self.config.jump_power     # 그냥 클릭 = 점프
            self.machine.change("fall")                  # 놓으면 중력으로 떨어짐
            if not self._moved:
                self._count_click()

    # ---------- 이스터에그 ----------
    def _count_click(self) -> None:
        now = time.monotonic()
        window = self.config.easter_egg_seconds
        self._clicks = [t for t in self._clicks if now - t <= window] + [now]
        if len(self._clicks) >= self.config.easter_egg_clicks:
            self._clicks.clear()
            self._find_easter_egg()

    def _find_easter_egg(self) -> None:
        name = characters.EASTER_EGG
        if self.config.character == name or not characters.has_images(self.config.sprites_root, name):
            return                                       # 이미 그 캐릭터거나, 이미지가 없는 PC
        characters.unlock_easter_egg()
        characters.set_active_character(name)
        self.change_character(name)
        self.ctx.say("짠! 물범이랑 같이 왔어", 120)
