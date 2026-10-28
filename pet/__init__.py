"""데스크톱 펫 패키지.

    pet.config   설정값
    pet.core     Qt를 모르는 로직 (상태, 현재 상태 값)
    pet.ui       Qt에 의존하는 부분 (위젯, 말풍선, 메뉴, 이미지 로딩, 화면 정보)

의존 방향은 ui -> core 한쪽뿐입니다.
"""
__version__ = "0.6.0"      # 바꿀 때 CHANGELOG.md와 git 태그(v0.6.0)도 함께
