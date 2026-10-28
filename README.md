# 데스크톱 펫 (PyQt5)

화면 아래(작업표시줄 위)를 돌아다니며 걷고, 앉고, 자고, 가끔 혼잣말을 하는 데스크톱 펫입니다.
이미지가 없으면 임시 도형 캐릭터로 실행되므로 설치 후 바로 실행해 볼 수 있습니다.

## 실행

Python 3.7 이상이 필요합니다 (3.12에서 확인).

```
pip install -r requirements.txt
python main.py [--character 폴더이름] [--size 128]
```

| 인자 | 설명 | 기본값 |
|---|---|---|
| `--character` | `sprites/` 아래 캐릭터 폴더 이름 | 설정 창에서 고른 캐릭터, 없으면 `default` |
| `--size` | 캐릭터 최대 크기(px). 더 큰 이미지는 축소 | 캐릭터의 `character.json`, 없으면 `128` |

## 조작

| 입력 | 동작 |
|---|---|
| 클릭 | 점프 (자는 중이면 깜짝 놀라며 깸) |
| 드래그 | 옮기기. 놓으면 그 모니터 바닥으로 떨어짐 (화면 밖에 놓으면 화면 안쪽으로) |
| 우클릭 | 메뉴 (점프 / 설정 / 업데이트 내역 / 종료) |

## 캐릭터 이미지

`sprites/<캐릭터>/` 폴더에 `walk_1.png`, `walk_2.png`, `idle.png`, `sleep.gif` 같은 이름으로 넣으면
자동으로 인식합니다. 자세한 파일 이름 규칙은 [sprites/default/README.txt](sprites/default/README.txt)를 보세요.

캐릭터 이미지(`sprites/` 아래 .png, .gif)는 저작권 때문에 저장소에 올리지 않습니다 (`.gitignore`).
이스터에그 캐릭터만 배포 파일(exe) 안에 숨겨서 넣습니다. 이 이미지는 넥슨 메이플스토리 캐릭터로,
넥슨 2차 창작 가이드라인에 따라 **비상업적 용도로만** 사용합니다. 이 프로그램을 판매하거나 수익을 내는 데 쓰지 마세요.
새로 받은 PC에서는 이미지를 직접 넣어야 하며, 없으면 임시 도형 캐릭터로 실행됩니다.

가장 쉬운 방법은 우클릭 → **설정**입니다. 캐릭터를 만들고 고르고, 동작별 이미지를 넣고, 아래 옵션을 바꿀 수 있습니다.

캐릭터마다 다른 설정은 같은 폴더의 `character.json`에 적습니다. `pet/config.py`의 설정 이름을 그대로 쓰며, 적은 값만 바뀝니다.

```json
{
    "faces_left": true,
    "max_size": 160,
    "frame_every": 4
}
```

`faces_left`는 이미지 속 캐릭터가 왼쪽을 보고 있을 때 `true`로 둡니다. 도트 그림은 축소하면 뭉개지므로 `max_size`를 가장 큰 이미지보다 크게 잡으세요.

## 구조

```
desktop_pet/
├── main.py                    진입점 (인자 처리, 객체 조립)
├── requirements.txt           의존 패키지 (PyQt5)
├── sprites/<캐릭터>/          캐릭터 이미지 (파일 이름 규칙은 sprites/default/README.txt)
└── pet/
    ├── config.py              크기·속도·중력·지속 시간·혼잣말 등 모든 설정값
    ├── core/                  Qt를 모르는 로직 (PyQt5 import 금지)
    │   ├── context.py         위치·속도·방향·애니메이션·말풍선 내용 (PetContext)
    │   └── states/
    │       ├── base.py        State, TimedState, StateMachine
    │       ├── transitions.py 상태 전환 가중치 표
    │       └── idle / walk / sit / sleep / fall / drag .py
    └── ui/                    Qt에 의존하는 부분
        ├── pet_widget.py      창 설정·그리기·마우스 입력
        ├── bubble.py          말풍선 (펫을 따라다니는 별도 투명 창)
        ├── characters.py      캐릭터 폴더 관리 (목록, 이미지 넣기·지우기, character.json, 사용 중인 캐릭터)
        ├── changelog.py       업데이트 내역 창 (CHANGELOG.md 표시), 새 버전 첫 실행 확인
        ├── menu.py            우클릭 메뉴 항목 목록
        ├── settings_dialog.py 설정 창 (캐릭터 선택, 이미지, 옵션)
        ├── single_instance.py 중복 실행 방지 (이미 실행 중이면 그 펫이 인사하고 종료)
        ├── updater.py         새 버전 확인 (GitHub Releases 최신 버전과 비교, 알림만)
        ├── sprites.py         이미지 로딩, 좌우 반전, 임시 도형 대체
        └── world.py           화면 경계·바닥 좌표 (모니터 정보는 실행 중에 읽어 옴)
```

의존 방향은 `ui → core` 한쪽뿐입니다. `core`는 위젯이나 화면을 직접 알지 못합니다.

## 자주 하는 수정

| 하고 싶은 일 | 고칠 곳 |
|---|---|
| 속도·크기·점프 높이·지속 시간 | `pet/config.py` |
| 애니메이션 프레임 속도 | `pet/config.py`의 `frame_every` (기본), `walk_frame_every`, `sleep_frame_every` |
| 혼잣말 내용·확률 | `pet/config.py`의 `idle_lines`, `idle_chat_chance` |
| 행동 확률 | `pet/core/states/transitions.py` |
| 새 행동 추가 | `pet/core/states/`에 파일 추가 → `__init__.py`의 `STATE_CLASSES` 등록 → `transitions.py`에 확률 추가 → `sprites/<캐릭터>/<이름>_1.png` (자세한 방법은 `pet/core/states/__init__.py`) |
| 우클릭 메뉴 항목 | `pet/ui/menu.py`의 `default_items` |
| 캐릭터 교체 | 우클릭 → 설정, 또는 `sprites/<이름>/` 폴더를 만들고 `--character <이름>` |
| 설정 창에 보이는 동작 목록 | `pet/ui/characters.py`의 `ANIMATIONS` |
| 이스터에그 캐릭터 | `pet/ui/characters.py`의 `EASTER_EGG` (찾기 전에는 설정 창에 안 보임) |
| 이스터에그 조건 (연타 횟수·시간) | `pet/config.py`의 `easter_egg_clicks`, `easter_egg_seconds` |

## 배포 파일 만들기

```
pip install -r requirements.txt pyinstaller
python build.py
```

`dist/DesktopPet-v<버전>-windows.zip`이 만들어집니다. 안에는 실행 파일(`DesktopPet.exe`)과 빈 `sprites/` 폴더만 있고,
캐릭터 이미지는 넣지 않습니다. 받은 사람은 zip을 풀고 exe를 실행하면 되며, Python 설치는 필요 없습니다.
캐릭터 이미지는 exe 옆 `sprites/` 폴더에 넣거나 설정 창으로 넣습니다.

GitHub에 올리려면 저장소의 Releases → "Draft a new release"에서 태그(예: `v0.6.0`)를 고르고 zip을 첨부합니다.
앱은 시작할 때 GitHub Releases의 최신 릴리스 태그를 확인해 지금 버전보다 새로우면 알려 줍니다
(설정 창에서 끌 수 있음). 그래서 릴리스 태그는 `v주.부.수` 형식이어야 합니다.

## 오류가 났을 때

처리되지 않은 오류는 앱을 끄지 않고 `error.log`에 기록합니다 (같은 오류는 한 번만).

| OS | 위치 |
|---|---|
| Windows | `%APPDATA%\desktop_pet\desktop_pet\error.log` |
| macOS | `~/Library/Application Support/desktop_pet/desktop_pet/error.log` |
| Linux | `~/.local/share/desktop_pet/desktop_pet/error.log` |

## 버전 관리

현재 버전은 `python main.py --version`으로 확인합니다. 버전별 변경 내용은 [CHANGELOG.md](CHANGELOG.md)에 있고,
앱에서는 우클릭 → "업데이트 내역"으로 같은 내용을 볼 수 있습니다. 새 버전으로 처음 실행하면 펫이 말풍선으로 알려 줍니다.

버전 번호는 `주.부.수` 형식입니다 ([유의적 버전](https://semver.org/lang/ko/)).
주는 기존 사용법이나 캐릭터 폴더 규칙이 호환되지 않게 바뀔 때, 부는 기능 추가, 수는 버그 수정입니다.

CHANGELOG.md는 앱 사용자에게 그대로 보이므로 코드, 파일 이름, 설정 이름, 명령어는 적지 않고 쉬운 말로만 씁니다.
개발 관련 내용은 커밋 메시지에 남깁니다.

작업 순서:

1. 기능마다 브랜치를 만듭니다: `git switch -c feature/<이름>` (버그 수정은 `fix/<이름>`)
2. 작업하면서 커밋하고, `CHANGELOG.md`의 `미반영` 아래에 바뀐 점을 적습니다.
3. 릴리스할 때 `pet/__init__.py`의 `__version__`을 올리고, `미반영`을 새 버전 번호와 날짜로 바꿉니다.
4. main에 합치고 태그를 붙입니다:
   ```
   git switch main
   git merge --no-ff feature/<이름>
   git tag -a v0.3.0 -m "v0.3.0"
   git push origin main --tags
   ```

특정 버전으로 돌아가 보려면 `git switch --detach v0.1.0`을 실행하고, 원래대로 돌아오려면 `git switch main`을 실행합니다.
