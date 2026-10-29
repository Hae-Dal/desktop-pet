"""설정 창의 '이미지' 칸: 동작별 미리보기, 찾아보기, 지우기.

고른 파일은 [적용]할 때까지 pending에만 기억해 둡니다.
"""
from typing import Dict, List, Optional

from PyQt5.QtCore import QBuffer, QByteArray, QSize, Qt
from PyQt5.QtGui import QImageReader, QMovie, QPixmap
from PyQt5.QtWidgets import QFileDialog, QFrame, QGridLayout, QGroupBox, QLabel, QMessageBox, QPushButton

from pet.ui import characters
from pet.ui.sprites import ANIMATED, EXTENSIONS

PREVIEW = 64           # 미리보기 칸 크기(px)
IMAGE_FILTER = "이미지 (%s)" % " ".join("*." + ext for ext in EXTENSIONS)
# 고를 수 있는 이미지 한도. 원본 그대로 읽은 뒤 줄이므로 너무 크면 켤 때 멈추거나 메모리가 모자람
# (4096x4096 한 장이 약 64MB). 폴더에 직접 넣은 파일은 검사하지 않음
MAX_PIXELS = 4096      # 가로·세로 각각
MAX_FRAMES = 300       # 움직이는 GIF·WebP 프레임 수


class ImagePanel(QGroupBox):
    def __init__(self):
        super().__init__("이미지")
        self.pending: Dict[str, Dict[str, Optional[str]]] = {}  # 캐릭터 폴더 -> 동작 -> 새 파일 (None이면 지움)
        self._char_dir: Optional[str] = None
        self._movies: List[QMovie] = []
        self._previews: Dict[str, QLabel] = {}

        grid = QGridLayout(self)
        for row, (anim, label) in enumerate(characters.ANIMATIONS):
            preview = QLabel()
            preview.setFixedSize(PREVIEW, PREVIEW)
            preview.setAlignment(Qt.AlignCenter)
            preview.setFrameShape(QFrame.StyledPanel)
            preview.setFrameShadow(QFrame.Sunken)
            browse = QPushButton("찾아보기...")
            browse.clicked.connect(lambda _, a=anim: self._browse(a))
            clear = QPushButton("지우기")
            clear.clicked.connect(lambda _, a=anim: self._choose(a, None))
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(preview, row, 1)
            grid.addWidget(browse, row, 2)
            grid.addWidget(clear, row, 3)
            self._previews[anim] = preview
        note = QLabel("이미지가 없는 동작은 '가만히 있기' 이미지로 대신합니다.")
        note.setEnabled(False)
        grid.addWidget(note, len(characters.ANIMATIONS), 0, 1, 4)

    def show_character(self, char_dir: Optional[str]) -> None:
        """그 캐릭터의 이미지를 보여 줌 (None이면 빈 칸)."""
        self._char_dir = char_dir
        self.setEnabled(bool(char_dir))
        for anim in self._previews:
            self._set_preview(anim, self._effective_file(anim) if char_dir else None)

    def forget(self, char_dir: str) -> None:
        """캐릭터를 지웠을 때 그 캐릭터의 미적용 변경도 버림."""
        self.pending.pop(char_dir, None)

    def apply(self) -> None:
        for char_dir, anims in self.pending.items():
            for anim, src in anims.items():
                if src:
                    characters.set_animation(char_dir, anim, src)
                else:
                    characters.clear_animation(char_dir, anim)
        self.pending.clear()

    def stop(self) -> None:
        """창을 닫을 때 GIF 미리보기 재생을 멈춤."""
        for movie in self._movies:
            movie.stop()

    def _effective_file(self, anim: str) -> Optional[str]:
        pending = self.pending.get(self._char_dir, {})
        if anim in pending:
            return pending[anim]
        return characters.animation_file(self._char_dir, anim)

    def _browse(self, anim: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", IMAGE_FILTER)
        if not path:
            return
        problem = check_image(path)
        if problem:
            QMessageBox.warning(self, "이미지 선택", problem)
            return
        self._choose(anim, path)

    def _choose(self, anim: str, path: Optional[str]) -> None:
        if not self._char_dir:
            return
        self.pending.setdefault(self._char_dir, {})[anim] = path
        self._set_preview(anim, path)

    def _set_preview(self, anim: str, path: Optional[str]) -> None:
        label = self._previews[anim]
        old = label.movie()
        if old:
            old.stop()
            self._movies.remove(old)
        label.setMovie(None)
        label.clear()
        if not path:
            label.setText("없음")
            return
        if path.lower().rsplit(".", 1)[-1] in ANIMATED:
            # 파일을 열어 둔 채로 두면 Windows에서 적용할 때 지우거나 덮어쓸 수 없어 메모리로 읽음
            with open(path, "rb") as f:
                buffer = QBuffer(self)
                buffer.setData(QByteArray(f.read()))
            movie = QMovie(buffer, QByteArray(), buffer)
            movie.jumpToFrame(0)
            movie.setScaledSize(_fit(movie.currentImage().size()))
            label.setMovie(movie)
            self._movies.append(movie)       # 참조를 잡아 두지 않으면 바로 사라짐
            movie.start()
        else:
            pix = QPixmap(path)
            label.setPixmap(pix.scaled(_fit(pix.size()), Qt.KeepAspectRatio, Qt.SmoothTransformation))


def check_image(path: str) -> Optional[str]:
    """넣을 수 없는 이미지면 그 이유, 괜찮으면 None. 크기·프레임 수는 이미지를 다 읽기 전에 확인."""
    reader = QImageReader(path)
    size = reader.size()
    if not size.isValid():
        return "이미지를 읽을 수 없습니다."
    if max(size.width(), size.height()) > MAX_PIXELS:
        return (f"이미지가 너무 큽니다 ({size.width()}×{size.height()}).\n"
                f"가로·세로 {MAX_PIXELS}px 이하로 줄여서 넣어 주세요.")
    if reader.imageCount() > MAX_FRAMES:
        return (f"프레임이 너무 많습니다 ({reader.imageCount()}장).\n"
                f"{MAX_FRAMES}장 이하로 줄여서 넣어 주세요.")
    if reader.read().isNull():
        return "이미지를 읽을 수 없습니다."
    return None


def _fit(size: QSize) -> QSize:
    """미리보기 칸에 들어가게 비율 유지 축소 (작은 이미지는 그대로)."""
    if size.width() <= PREVIEW and size.height() <= PREVIEW:
        return size
    return size.scaled(PREVIEW, PREVIEW, Qt.KeepAspectRatio)
