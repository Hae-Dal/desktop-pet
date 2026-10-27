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
| `--character` | `sprites/` 아래 캐릭터 폴더 이름 | `default` |
| `--size` | 캐릭터 최대 크기(px). 더 큰 이미지는 축소 | `128` |

## 조작

| 입력 | 동작 |
|---|---|
| 클릭 | 점프 (자는 중이면 깜짝 놀라며 깸) |
| 드래그 | 옮기기. 놓으면 바닥으로 떨어짐 (화면 밖에 놓으면 화면 안쪽으로) |
| 우클릭 | 메뉴 (점프 / 종료) |

## 캐릭터 이미지

`sprites/<캐릭터>/` 폴더에 `walk_1.png`, `walk_2.png`, `idle.png`, `sleep.gif` 같은 이름으로 넣으면
자동으로 인식합니다. 자세한 파일 이름 규칙은 [sprites/default/README.txt](sprites/default/README.txt)를 보세요.

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
        ├── menu.py            우클릭 메뉴 항목 목록
        ├── sprites.py         이미지 로딩, 좌우 반전, 임시 도형 대체
        └── world.py           화면 경계·바닥 좌표 (멀티 모니터 대응 시 여기만 수정)
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
| 캐릭터 교체 | `sprites/<이름>/` 폴더를 만들고 `--character <이름>` |
