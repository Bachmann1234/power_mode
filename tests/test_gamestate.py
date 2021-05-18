from datetime import timedelta
from time import time

import freezegun
from pynput.keyboard import Key, KeyCode

from power_mode.main import GameState


@freezegun.freeze_time("2020-05-17 10:12:34")
def test_create_gamestate():
    assert GameState.start() == GameState(
        current_combo=0,
        max_combo=0,
        max_median_wpm=0,
        combo_at_last_timeout=0,
        median_wpm_at_last_timeout=0,
        combo_timeout=10,
        time_of_last_key=1589710344.0,
        combo_start=1589710354.0,
        recorded_wpms=[],
        num_backspaces=0,
    )


def test_percent_time_left():
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        gamestate = GameState.start().increment_combo(KeyCode.from_char("a"))
        assert gamestate.percent_time_left == 1
        frozen_time.tick(delta=timedelta(seconds=5))
        assert gamestate.percent_time_left == 0.5
        frozen_time.tick(delta=timedelta(seconds=5))
        assert gamestate.percent_time_left == 0
        frozen_time.tick(delta=timedelta(seconds=1))
        assert gamestate.percent_time_left == 0


def test_current_wpm():
    assert GameState.start().current_wpm == 0
    assert GameState.start().copy(current_combo=24).current_wpm == 0
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        gamestate = GameState.start()
        frozen_time.tick(delta=timedelta(minutes=1))
        assert gamestate.copy(current_combo=100).current_wpm == 20
        # Yep, I floor it
        assert gamestate.copy(current_combo=99).current_wpm == 19


def test_median_wpm():
    assert GameState.start().copy(recorded_wpms=[10, 20, 30]).median_wpm == 20


def test_increment_combo():
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        gamestate = GameState.start().increment_combo(KeyCode.from_char("a"))
        assert gamestate.current_combo == 1
        assert gamestate.num_backspaces == 0
        gamestate = gamestate.increment_combo(Key.backspace)
        assert gamestate.current_combo == 2
        assert gamestate.num_backspaces == 1
        assert gamestate.time_of_last_key == 1589710354.0
        frozen_time.tick(delta=timedelta(seconds=1))
        gamestate = gamestate.increment_combo(KeyCode.from_char("b"))
        assert gamestate.current_combo == 3
        assert gamestate.num_backspaces == 1
        assert gamestate.time_of_last_key == 1589710355.0


def test_increment_combo_from_zero_resets_recorded_wpm():
    assert (
        GameState.start()
        .copy(recorded_wpms=[1, 2, 3])
        .increment_combo(KeyCode.from_char("a"))
        .recorded_wpms
        == []
    )


def test_combo_stopped():
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        gamestate = GameState.start().copy(
            current_combo=1000,
            time_of_last_key=time(),
            num_backspaces=100,
            max_combo=100,
            recorded_wpms=[1, 2, 3],
        )
        frozen_time.tick(delta=timedelta(seconds=100))
        gamestate = gamestate.increment_combo(KeyCode.from_char("a")).record_wpm()
        gamestate = gamestate.combo_stopped()
        assert gamestate == GameState(
            current_combo=0,
            max_combo=1001,
            max_median_wpm=2,
            combo_at_last_timeout=1001,
            median_wpm_at_last_timeout=2,
            combo_timeout=10,
            time_of_last_key=1589710454.0,
            combo_start=1589710454.0,
            recorded_wpms=[],
            num_backspaces=0,
        )
        # Calling it multiple times should not change things
        assert gamestate.combo_stopped() == gamestate.combo_stopped()


def test_record_wpm():
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        gamestate = GameState.start()
        frozen_time.tick(delta=timedelta(minutes=1))
        gamestate = gamestate.copy(current_combo=100)
        assert gamestate.current_wpm == 20
        assert gamestate.record_wpm().recorded_wpms == [20]
        hundred_and_first_recording = gamestate.copy(
            recorded_wpms=[100 for _ in range(100)]
        ).record_wpm()
        assert len(hundred_and_first_recording.recorded_wpms) == 100
        assert hundred_and_first_recording.recorded_wpms[-1] == 20
