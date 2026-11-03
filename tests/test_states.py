"""행동 상태 (Qt 없이 동작하는 부분)."""
import random

import pytest

from pet.config import PetConfig, greeting_for
from pet.core.context import PetContext
from pet.core.states import StateMachine, build_states


@pytest.fixture
def pet(world):
    ctx = PetContext(PetConfig(), world, 40, 40)
    ctx.x = 100
    ctx.snap_to_ground()
    machine = StateMachine(build_states(ctx))
    return ctx, machine


def run_until_ground(machine, ctx, limit=500):
    for _ in range(limit):
        machine.update()
        if machine.current_name != "fall" and machine.current_name != "jump":
            return
    raise AssertionError("착지하지 않음")


def test_unknown_state_falls_back_to_idle(pet):
    ctx, machine = pet
    machine.change("dance")
    assert machine.current_name == "idle"


def test_timed_state_moves_on_when_time_is_up(pet):
    ctx, machine = pet
    random.seed(1)
    machine.change("idle")
    seen = set()
    for _ in range(2000):
        machine.update()
        seen.add(machine.current_name)
    assert {"idle", "walk"} <= seen
    assert seen <= {"idle", "walk", "sit", "sleep", "jump"}


def test_falls_when_in_the_air(pet):
    ctx, machine = pet
    machine.change("idle")
    ctx.y -= 200
    machine.update()
    assert machine.current_name == "fall"
    run_until_ground(machine, ctx)
    assert ctx.y == ctx.ground_y and ctx.vy == 0


def test_walk_turns_around_at_edges(pet, world):
    ctx, machine = pet
    machine.change("walk")
    ctx.facing, ctx.x = 1, world.width - ctx.width - 1
    machine.current._remaining = 100
    for _ in range(5):
        machine.update()
    assert ctx.facing == -1
    assert ctx.x <= world.width - ctx.width


def test_jump_from_walk_moves_forward(pet):
    ctx, machine = pet
    machine.change("walk")
    ctx.facing = 1
    machine.change("jump")
    assert ctx.vy < 0 and ctx.vx > 0
    start = ctx.x
    run_until_ground(machine, ctx)
    assert ctx.x > start and ctx.vx == 0


def test_jump_from_idle_goes_straight_up(pet):
    ctx, machine = pet
    machine.change("idle")
    machine.change("jump")
    assert ctx.vy < 0 and ctx.vx == 0


def test_sleep_shows_zzz_until_it_wakes(pet):
    ctx, machine = pet
    machine.change("sleep")
    assert ctx.bubble_text == "Zzz..."
    machine.change("idle")
    assert ctx.bubble_text == "" or ctx.bubble_text in PetConfig().lines_for("idle")


def test_drag_stops_movement(pet):
    ctx, machine = pet
    ctx.vx, ctx.vy = 3.0, -5
    machine.change("drag")
    assert ctx.vx == 0 and ctx.vy == 0
    ctx.y -= 50                         # 잡고 있는 동안은 떨어지지 않음
    machine.update()
    assert machine.current_name == "drag"


def test_idle_chat_uses_character_lines(world):
    config = PetConfig(idle_chat_chance=1.0, lines={"idle": ("안녕",)})
    ctx = PetContext(config, world, 40, 40)
    ctx.snap_to_ground()
    machine = StateMachine(build_states(ctx))
    machine.change("idle")
    assert ctx.bubble_text == "안녕"


def test_idle_chat_never_when_chance_zero(world):
    ctx = PetContext(PetConfig(idle_chat_chance=0.0), world, 40, 40)
    machine = StateMachine(build_states(ctx))
    for _ in range(20):
        machine.change("idle")
        assert ctx.bubble_text == ""


def sleeping_pet(world, **settings):
    ctx = PetContext(PetConfig(sleep_ticks=(1, 1), **settings), world, 40, 40)
    ctx.snap_to_ground()
    machine = StateMachine(build_states(ctx))
    machine.change("sleep")
    return ctx, machine


def test_says_a_line_when_waking_up_alone(world):
    ctx, machine = sleeping_pet(world, idle_chat_chance=1.0, lines={"wake": ("잘 잤다",)})
    machine.update()
    assert machine.current_name != "sleep" and ctx.bubble_text == "잘 잤다"


def test_being_woken_is_not_waking_up_alone(world):
    ctx, machine = sleeping_pet(world, idle_chat_chance=1.0, lines={"wake": ("잘 잤다",)})
    machine.change("drag")
    assert ctx.bubble_text == ""


def test_character_can_change_sleep_line(world):
    ctx, machine = sleeping_pet(world, lines={"sleep": ("쿨쿨",)})
    assert ctx.bubble_text == "쿨쿨"


def test_sleep_line_shows_even_when_chance_is_zero(world):
    ctx, machine = sleeping_pet(world, idle_chat_chance=0.0)
    assert ctx.bubble_text == "Zzz..."


def lonely_pet(world, chance):
    config = PetConfig(idle_chat_chance=chance, lonely_ticks=100, lines={"idle": ("혼잣말",), "lonely": ("심심해",)})
    ctx = PetContext(config, world, 40, 40)
    ctx.snap_to_ground()
    return ctx, StateMachine(build_states(ctx))


def test_lonely_after_being_left_alone_then_counts_again(world):
    ctx, machine = lonely_pet(world, 1.0)
    machine.change("idle")
    assert ctx.bubble_text == "혼잣말"
    ctx.clear_bubble()
    ctx.untouched_ticks = 100
    machine.change("idle")
    assert ctx.bubble_text == "심심해" and ctx.untouched_ticks == 0
    ctx.clear_bubble()
    machine.change("idle")
    assert ctx.bubble_text == "혼잣말"


def test_never_lonely_out_loud_when_chance_is_zero(world):
    ctx, machine = lonely_pet(world, 0.0)
    ctx.untouched_ticks = 100
    machine.change("idle")
    assert ctx.bubble_text == ""


def test_notice_survives_lines_and_wake_up_then_ends(world):
    ctx, machine = sleeping_pet(world, idle_chat_chance=1.0)
    ctx.notify("안내", 2)
    machine.change("idle")                      # 자다가 깨면 Zzz는 지워지지만 안내는 남음
    assert ctx.bubble_text == "안내"
    ctx.say_line("click")
    assert ctx.bubble_text == "안내"
    ctx.tick_bubble()
    ctx.tick_bubble()
    assert ctx.bubble_text == ""
    ctx.say_line("click")
    assert ctx.bubble_text in PetConfig().lines_for("click")


@pytest.mark.parametrize("hour, situation", [
    (5, "morning"), (10, "morning"), (11, "afternoon"), (16, "afternoon"),
    (17, "evening"), (21, "evening"), (22, "night"), (0, "night"), (4, "night"),
])
def test_greeting_by_hour(hour, situation):
    assert greeting_for(hour) == situation


def run_states(config, world, ticks=3000):
    random.seed(7)
    ctx = PetContext(config, world, 40, 40)
    ctx.snap_to_ground()
    machine = StateMachine(build_states(ctx))
    machine.change("idle")
    seen = []
    for _ in range(ticks):
        machine.update()
        seen.append(machine.current_name)
    return seen


def test_character_can_turn_off_a_behavior(world):
    no_walk = {"idle": {"walk": 0, "jump": 0}}
    seen = run_states(PetConfig(transitions=no_walk), world)
    assert "walk" not in seen and "jump" not in seen and "sit" in seen


def test_sleepy_character_sleeps_more(world):
    normal = run_states(PetConfig(), world).count("sleep")
    sleepy = run_states(PetConfig(transitions={"idle": {"sleep": 5}, "sit": {"sleep": 5}}), world).count("sleep")
    assert sleepy > normal * 2


def test_all_zero_weights_keep_current_behavior(world):
    seen = run_states(PetConfig(transitions={"idle": {"walk": 0, "sit": 0, "sleep": 0, "jump": 0}}), world, 500)
    assert set(seen) == {"idle"}
