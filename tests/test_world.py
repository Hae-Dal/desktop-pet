"""화면 경계와 바닥 계산 (모니터 구성은 가짜로 넣음)."""
import pytest
from PyQt5.QtCore import QRect

from pet.ui.world import World


def world_with(*rects):
    w = World()
    w.screens = lambda: [QRect(*r) for r in rects]
    return w


SIDE_BY_SIDE = ((0, 0, 1920, 1040), (1920, 0, 1280, 984))     # 오른쪽 모니터가 작고 작업표시줄도 다름


def test_whole_area_spans_all_monitors():
    w = world_with(*SIDE_BY_SIDE)
    assert w.x_range(100) == (0, 1920 + 1280 - 100)


@pytest.mark.parametrize("x, ground", [(100, 1040 - 50), (2500, 984 - 50)])
def test_ground_is_the_monitor_under_the_pet(x, ground):
    w = world_with(*SIDE_BY_SIDE)
    assert w.ground_y(x, 0, 50, 50) == ground


def test_gap_between_monitors_uses_nearest():
    w = world_with((0, 0, 1000, 800), (1200, 0, 1000, 600))
    assert w.area_at(1010, 0, 0, 0).left() == 0
    assert w.area_at(1190, 0, 0, 0).left() == 1200


def test_stacked_monitors_fall_to_lower_one():
    w = world_with((0, 0, 1000, 800), (0, 800, 1000, 800))
    assert w.area_at(10, 10, 20, 20).top() == 0
    assert w.area_at(10, 900, 20, 20).top() == 800
