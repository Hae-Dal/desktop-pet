이 폴더에 캐릭터 이미지를 넣으세요. (오른쪽을 보는 이미지 기준 — 왼쪽은 자동 반전)
형식: PNG, GIF, WebP, JPG, BMP. JPG와 BMP는 배경을 투명하게 할 수 없어 네모난 배경이 그대로 보입니다.

  walk_1.png, walk_2.png, ...   걷기 프레임 (번호순)  또는  walk.gif
  idle.png                      가만히 있을 때 (선택, 없으면 walk 첫 프레임)
  sit_1.png ... / sit.gif       앉기 (선택, 없으면 idle로 대체)
  sleep_1.png ... / sleep.gif   잠자기 (선택, 없으면 idle로 대체)
  fall.png / drag.png           점프·떨어짐 / 잡혔을 때 (선택, 없으면 idle로 대체)
  <새이름>_1.png ...            pet/core/states/에 새 상태를 추가했다면 같은 이름으로

파일 이름 규칙
  - <이름>_<번호>.<형식> 또는 <이름>.<형식>  (예: walk_1.png, idle.webp, sit.gif)
  - 대소문자는 구분하지 않습니다 (Walk_1.PNG = walk_1.png).
  - 번호는 숫자 크기순으로 재생됩니다 (1, 2, ..., 10).
  - 이름에 '_'를 써도 됩니다 (sleep_left_1.png -> "sleep_left").
  - 같은 이름이 여러 형식으로 있으면 번호 붙은 파일 > png > webp > gif > jpg > bmp 순으로 하나만 씁니다.
    (번호 붙은 파일은 첫 프레임만 쓰이므로, 움직이는 GIF·WebP는 번호 없이 <이름>.gif로 넣으세요.)
  - 이미지는 가로·세로 4096px 이하, 움직이는 이미지는 300프레임 이하로 넣으세요.
    (설정 창은 이보다 큰 이미지를 받지 않습니다. 화면에는 캐릭터 최대 크기로 줄여서 보입니다.)
  - 크기가 다른 이미지를 섞어도 되지만, 바닥 기준 가운데 정렬되므로 캔버스 크기를 맞추면 깔끔합니다.

다른 캐릭터를 쓰려면 sprites/ 아래에 새 폴더(예: sprites/mychar)를 만들고
    python main.py --character mychar
로 실행하세요.

캐릭터별 설정(왼쪽을 보는 이미지, 크기, 애니메이션 속도)은 character.json에 적습니다.
프로젝트 README.md의 "캐릭터 이미지" 항목을 보세요.

이 폴더가 비어 있으면 임시 도형 캐릭터로 실행됩니다. 이 README.txt는 무시됩니다.
