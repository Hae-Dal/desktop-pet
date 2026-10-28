"""배포용 실행 파일 만들기 (PyInstaller).

    python build.py

dist/DesktopPet-v<버전>-<OS>.zip 이 만들어집니다. 안에는 실행 파일과 빈 sprites/ 폴더가 들어갑니다.
이스터에그 캐릭터(sprites/<EASTER_EGG>/)는 이 PC에 있으면 exe 안에 숨겨서 넣습니다 (비상업 2차 창작 조건).
그 외 캐릭터 이미지는 넣지 않습니다. 필요한 패키지: pip install -r requirements.txt pyinstaller
"""
import os
import platform
import shutil
import subprocess
import sys

from pet import __version__
from pet.ui.characters import EASTER_EGG

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
NAME = "DesktopPet"


def main() -> int:
    egg = os.path.join(ROOT, "sprites", EASTER_EGG)
    bundled = []
    if os.path.isdir(egg):
        bundled = ["--add-data", egg + os.pathsep + os.path.join("bundled_sprites", EASTER_EGG)]
    else:
        print(f"경고: {egg} 가 없어 이스터에그 캐릭터 없이 빌드합니다.")

    subprocess.run([
        sys.executable, "-m", "PyInstaller", os.path.join(ROOT, "main.py"),
        "--name", NAME,
        "--onefile",                     # exe 하나로
        "--windowed",                    # 콘솔 창 없이
        "--add-data", os.path.join(ROOT, "CHANGELOG.md") + os.pathsep + ".",
        *bundled,
        "--distpath", os.path.join(BUILD, "dist"),
        "--workpath", os.path.join(BUILD, "work"),
        "--specpath", BUILD,
        "--noconfirm", "--clean",
    ], check=True)

    release = f"{NAME}-v{__version__}-{platform.system().lower()}"
    folder = os.path.join(DIST, release)
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(os.path.join(folder, "sprites", "default"))
    exe = NAME + (".exe" if os.name == "nt" else "")
    shutil.copy2(os.path.join(BUILD, "dist", exe), folder)
    shutil.copy2(os.path.join(ROOT, "sprites", "default", "README.txt"),
                 os.path.join(folder, "sprites", "default"))

    archive = shutil.make_archive(folder, "zip", DIST, release)
    print(f"\n완료: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
