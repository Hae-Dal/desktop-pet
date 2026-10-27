"""창 설정, 그리기, 마우스 입력만 담당합니다. 행동 판단은 pet/core/states가 합니다."""
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QWidget

from pet.config import PetConfig
from pet.core.context import PetContext
from pet.core.states import StateMachine, TimedState, build_states
from pet.ui import menu
from pet.ui.bubble import BubbleWidget
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

        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._moved = False

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
        self.bubble.follow(self.frameGeometry(), self.ctx.world.area())
        if not self.bubble.isVisible():
            self.bubble.show()

    # ---------- 동작 ----------
    def jump(self) -> None:
        if isinstance(self.machine.current, TimedState) and self.ctx.on_ground:
            self.ctx.vy = self.config.jump_power
            self.machine.change("fall")

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
