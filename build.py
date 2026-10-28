"""배포용 실행 파일 만들기 (PyInstaller).

    python build.py

dist/DesktopPet-v<버전>-<OS>.zip 이 만들어집니다. 안에는 실행 파일과 빈 sprites/ 폴더가 들어가며
캐릭터 이미지는 저작권 때문에 넣지 않습니다. 필요한 패키지: pip install -r requirements.txt pyinstaller
"""
import os
import platform
import shutil
import subprocess
import sys

from pet import __version__

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
NAME = "DesktopPet"


def main() -> int:
    subprocess.run([
        sys.executable, "-m", "PyInstaller", os.path.join(ROOT, "main.py"),
        "--name", NAME,
        "--onefile",                     # exe 하나로
        "--windowed",                    # 콘솔 창 없이
        "--add-data", os.path.join(ROOT, "CHANGELOG.md") + os.pathsep + ".",
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
