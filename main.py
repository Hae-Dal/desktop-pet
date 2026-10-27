"""진입점. 프로젝트 폴더에서 실행하세요.

    python main.py                       # sprites/default/ 의 캐릭터로 실행
    python main.py --character pikachu   # sprites/pikachu/ 폴더의 캐릭터로 실행
    python main.py --size 96             # 캐릭터 최대 크기(px) 변경
"""
import argparse
import sys

from PyQt5.QtWidgets import QApplication

from pet.config import PetConfig
from pet.ui.pet_widget import PetWidget
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


def parse_args() -> argparse.Namespace:
    defaults = PetConfig()
    parser = argparse.ArgumentParser(description="데스크톱 펫")
    parser.add_argument("--character", default=defaults.character,
                        help="sprites/ 아래 캐릭터 폴더 이름 (기본: %(default)s)")
    parser.add_argument("--size", type=int, default=defaults.max_size,
                        help="캐릭터 최대 크기(px) (기본: %(default)s)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = PetConfig(character=args.character, max_size=args.size)

    app = QApplication(sys.argv)          # QPixmap 생성보다 먼저 만들어야 함
    sprites = SpriteSet.load(config)
    pet = PetWidget(config, sprites, World())
    pet.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
