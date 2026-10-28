"""진입점. 프로젝트 폴더에서 실행하세요.

    python main.py                       # 설정 창에서 고른 캐릭터로 실행 (처음엔 sprites/default/)
    python main.py --character pikachu   # sprites/pikachu/ 폴더의 캐릭터로 실행
    python main.py --size 96             # 캐릭터 최대 크기(px) 변경
"""
import argparse
import os
import sys
from dataclasses import replace
from typing import Optional

from PyQt5.QtWidgets import QApplication

from pet import __version__
from pet.config import PetConfig
from pet.ui import characters, errorlog
from pet.ui.pet_widget import PetWidget
from pet.ui.single_instance import SingleInstance
from pet.ui.sprites import SpriteSet
from pet.ui.world import World


def parse_args() -> argparse.Namespace:
    defaults = PetConfig()
    parser = argparse.ArgumentParser(description="데스크톱 펫")
    parser.add_argument("--character",
                        help=f"sprites/ 아래 캐릭터 폴더 이름 (기본: 설정 창에서 고른 캐릭터, 없으면 {defaults.character})")
    parser.add_argument("--size", type=int,
                        help=f"캐릭터 최대 크기(px) (기본: character.json 또는 {defaults.max_size})")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def _saved_character() -> Optional[str]:
    """설정 창에서 마지막으로 고른 캐릭터. 폴더가 지워졌으면 None."""
    name = characters.active_character()
    if name and os.path.isdir(os.path.join(PetConfig().sprites_root, name)):
        return name
    return None


def main() -> int:
    args = parse_args()
    character = args.character or _saved_character() or PetConfig().character
    config = PetConfig(character=character).with_character_settings()   # 기본값 < character.json < 인자
    if args.size:
        config = replace(config, max_size=args.size)

    app = QApplication(sys.argv)          # QPixmap 생성보다 먼저 만들어야 함
    app.setOrganizationName("desktop_pet")
    app.setApplicationName("desktop_pet")
    errorlog.install()                    # 오류가 나도 꺼지지 않고 error.log에 기록
    instance = SingleInstance()
    if not instance.acquire():            # 이미 실행 중이면 그 펫이 대신 인사하고 여기선 종료
        return 0
    sprites = SpriteSet.load(config)
    pet = PetWidget(config, sprites, World())
    instance.activated.connect(pet.greet)
    pet.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
