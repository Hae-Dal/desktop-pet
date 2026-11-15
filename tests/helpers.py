"""여러 테스트 파일이 같이 쓰는 도우미 (pytest가 tests/를 import 경로에 넣어 줌)."""
from PyQt5.QtGui import QColor, QImage


def save_image(path, w: int = 10, h: int = 10, color: str = "red") -> str:
    """단색 이미지 파일을 만들고 그 경로를 돌려줌. 형식은 확장자로 정해짐 (png, bmp, ...)."""
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(QColor(color))
    assert img.save(str(path))
    return str(path)
