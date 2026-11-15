# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PyQt5 데스크톱 펫 (Windows 위주, GitHub: Hae-Dal/desktop-pet). 코드 주석·문서·커밋 메시지는 모두 한국어로 씁니다.

## 명령

Python은 `.venv`의 것을 씁니다 (PyQt5 5.15, pytest, pyflakes, pyinstaller가 들어 있음).

```
.venv/Scripts/python.exe main.py [--character 폴더이름] [--size 128]   # 실행
.venv/Scripts/python.exe -m pytest -q                                   # 전체 테스트 (화면 없이 offscreen)
.venv/Scripts/python.exe -m pytest tests/test_states.py::test_이름      # 테스트 하나
.venv/Scripts/python.exe -m pyflakes pet tests main.py                  # 린트
.venv/Scripts/python.exe build.py                                       # dist/DesktopPet-v<버전>-windows.zip
```

- README가 Python 3.7 이상을 지원한다고 적고 있으므로 walrus(`:=`) 같은 3.8+ 문법은 쓰지 않습니다.
- `main.py`를 실행하면 실제 사용자 저장값(레지스트리)과 단일 실행 잠금을 씁니다. 화면 확인만 필요하면 `prefs.override_file`, `autostart.override_file`을 임시 파일로 정한 스크립트에서 위젯을 만들어 `widget.grab().save(...)`로 그려 봅니다.
- 테스트는 `tests/conftest.py`가 `prefs`·`autostart` 저장 위치를 임시 파일로 바꿔 줍니다. 펫 창이 필요하면 conftest의 `make_pet` fixture를 쓰고 (새 버전 확인과 "업데이트됐어" 안내를 꺼 둠, 끝나면 닫음), 테스트용 이미지 파일은 `tests/helpers.py`의 `save_image`로 만듭니다.

## 구조

의존 방향은 `pet/ui → pet/core` 한쪽뿐이고, `pet/core`는 PyQt5를 import하지 않습니다 (Qt 없이 테스트 가능).

- **`pet/config.py`**: 모든 기본값(`PetConfig` dataclass), 기본 대사 `DEFAULT_LINES`, 행동 가중치 `DEFAULT_TRANSITIONS`, 캐릭터별 `character.json` 읽기. `character.json`은 `read_character_file`에서만 읽고 `pet/ui/characters.py`의 `write_settings`에서만 씁니다. 손으로 고친 파일이 깨져도 켜지도록 형식이 틀린 값은 `_fix`/`_clean`이 걸러 내므로, `PetConfig`에 dict 같은 새 필드를 넣으면 `_fix`에도 검사를 추가합니다.
- **`pet/core/context.py` (`PetContext`)**: 위치·속도·애니메이션·말풍선 상태. 말풍선은 세 종류입니다.
  - `say`/`say_line`: 펫의 말. 안내가 떠 있거나 "조용히 하기" 중이면 무시됨.
  - `notify`: 프로그램 안내(새 버전 등). 끝날 때까지 대사로 덮이거나 지워지지 않음.
  - `react_line`(만졌을 때, 확률 0이면 안 함) / `chat_line`·`chat`(혼자 하는 말, `idle_chat_chance` 확률).
- **`pet/core/states/`**: 상태 머신. `TimedState`는 시간이 끝나면 `config.transitions_for(state)` 가중치로 다음 행동을 고릅니다. 가중치 = `DEFAULT_TRANSITIONS` ← `character.json`의 `transitions`로 덮어쓰기 → `often`(행동별 배수) 곱하기. 새 행동 추가 방법은 `pet/core/states/__init__.py` 맨 위에 있습니다.
- **`pet/ui/pet_widget.py`**: 펫 창. 30ms 타이머로 `machine.update()` → 말풍선 → 이동. 마우스 입력, 캐릭터 바꾸기(`change_character`)·크기 바꾸기(`set_scale`)는 `_reload`로 이미지와 상태들을 새로 만듭니다 (상태들이 설정값을 생성 시점에 읽어 두기 때문).
- **`pet/ui/sprites.py`**: `sprites/<캐릭터>/` 파일 이름(`walk_1.png`, `sit.gif` 등)으로 애니메이션을 자동 인식. 없는 애니메이션은 `SUBSTITUTES`(jump↔fall) → `idle` 순으로 대체.
- **`pet/ui/settings/`**: 설정 창. 캐릭터별 칸(`OptionsPanel`, `PersonalityPanel`, `LinesPanel`)은 모두 `load(values)` / `changes(saved)` 규약을 따르고, `dialog.py`가 바뀐 값만 모아 [적용] 때 한꺼번에 씁니다. 사용자가 건드리지 않은 값은 파일에 쓰지 않는 것이 원칙입니다 (테스트로 확인함).
- **`pet/ui/prefs.py`**: 앱 전체 저장값(QSettings). 캐릭터별 값은 여기가 아니라 `character.json`.
- **`pet/ui/menu.py`**: 우클릭·트레이 메뉴 항목 목록 (`MenuItem`, 하위 메뉴·체크 지원, `fill`로 QMenu에 넣음).
- 이스터에그 캐릭터(`pet/ui/easter_egg.py`의 `NAME`)는 `build.py`가 exe 안에 숨겨 넣고, 찾으면 `sprites/`로 꺼냅니다.

## 작업 규칙

- 기능마다 `feature/<이름>` (버그는 `fix/<이름>`) 브랜치에서 작업하고, main에는 `git merge --no-ff`로 합칩니다. 다 쓴 브랜치도 지우지 않습니다. 푸시와 릴리스는 사용자가 요청할 때만 합니다.
- 새 코드를 쓰기 전에 이미 있는 추상화와 재사용할 수 있는 코드를 먼저 찾아 그것을 우선으로 씁니다. 비슷한 일을 하는 코드를 새로 만들지 않습니다. 예를 들어 대사는 `ctx.say_line`/`react_line`/`chat_line`, 메뉴는 `MenuItem`과 `menu.fill`, 설정 창 칸은 `load`/`changes` 규약, `character.json` 읽기·쓰기는 `read_character_file`/`write_settings`, 이미지 검사는 `check_image`를 씁니다. 맞는 것이 없으면 기존 것을 넓히는 방법을 먼저 검토하고, 같은 코드가 두 곳 이상에 생기면 공용 함수로 묶습니다.
- `CHANGELOG.md`는 앱의 "업데이트 내역" 창에 그대로 보입니다. `미반영` 아래에 사용자 눈에 보이는 변화만 쉬운 말로 적고, 코드·파일 이름·설정 이름·명령어는 절대 적지 않습니다 (개발 내용은 커밋 메시지에). 릴리스할 때 `pet/__init__.py`의 `__version__`을 올리고 `미반영`을 `## <버전> - <날짜>`로 바꿉니다. 릴리스 태그는 앱의 새 버전 확인 때문에 반드시 `v주.부.수` 형식입니다.
- `sprites/` 아래 이미지 파일은 저작권 때문에 git에 올리지 않습니다 (`.gitignore`). 이스터에그 캐릭터 이미지는 메이플스토리 2차 창작이라 비상업적 용도로만 씁니다.
- `sprites/` 아래 `character.json`이나 캐릭터 폴더에 생긴 로컬 변경은 사용자가 테스트하며 바꾼 것이므로 커밋에 넣지 않습니다. `git add`는 경로를 지정해서 합니다 (`git add -A` 금지). `build.py`는 이스터에그 폴더에 커밋 안 된 변경이 있으면 그대로 exe에 들어간다고 경고합니다.
- Bash heredoc 안의 Python 문자열에 `\\n`을 쓰면 실제 줄바꿈으로 바뀌어 문법 오류가 납니다. `\n`이 들어가는 문자열 수정은 Edit 도구로 합니다.
- PyInstaller onefile exe는 부트로더와 자식 프로세스 두 개로 뜹니다. 테스트로 띄운 exe를 끌 때 부트로더만 끄면 자식이 남아 단일 실행 잠금 때문에 다음 실행이 막히므로, 실행 파일 경로로 두 프로세스를 모두 끕니다.
