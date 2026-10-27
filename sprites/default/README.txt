이 폴더에 캐릭터 이미지를 넣으세요. (배경 투명 PNG/GIF, 오른쪽을 보는 이미지 기준 — 왼쪽은 자동 반전)

  walk_1.png, walk_2.png, ...   걷기 프레임 (번호순)  또는  walk.gif
  idle.png                      가만히 있을 때 (선택, 없으면 walk 첫 프레임)
  sit_1.png ... / sit.gif       앉기 (선택, 없으면 idle로 대체)
  sleep_1.png ... / sleep.gif   잠자기 (선택, 없으면 idle로 대체)
  fall.png / drag.png           점프·떨어짐 / 잡혔을 때 (선택, 없으면 idle로 대체)
  <새이름>_1.png ...            pet/core/states/에 새 상태를 추가했다면 같은 이름으로

파일 이름 규칙
  - <이름>_<번호>.png 또는 <이름>.png 또는 <이름>.gif
  - 대소문자는 구분하지 않습니다 (Walk_1.PNG = walk_1.png).
  - 번호는 숫자 크기순으로 재생됩니다 (1, 2, ..., 10).
  - 이름에 '_'를 써도 됩니다 (sleep_left_1.png -> "sleep_left").
  - 같은 이름이 여러 형식으로 있으면 번호 붙은 파일 > <이름>.png > <이름>.gif 순으로 하나만 씁니다.
    (번호 붙은 .gif는 첫 프레임만 쓰이므로, 움직이는 GIF는 번호 없이 <이름>.gif로 넣으세요.)
  - 크기가 다른 이미지를 섞어도 되지만, 바닥 기준 가운데 정렬되므로 캔버스 크기를 맞추면 깔끔합니다.

다른 캐릭터를 쓰려면 sprites/ 아래에 새 폴더(예: sprites/mychar)를 만들고
    python main.py --character mychar
로 실행하세요.

이 폴더가 비어 있으면 임시 도형 캐릭터로 실행됩니다. 이 README.txt는 무시됩니다.
