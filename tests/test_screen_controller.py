from datetime import timedelta
from time import time
from unittest.mock import Mock, call

import freezegun
from pynput.keyboard import KeyCode

from power_mode.main import GameState, ScreenController


def test_screen_tick():
    mock_serial = Mock()
    controller = ScreenController(mock_serial)
    controller.key_down(None, GameState.start())
    assert mock_serial.write.call_args_list == []


def test_tick():
    mock_serial = Mock()
    with freezegun.freeze_time("2020-05-17 10:12:34"):
        # Start
        game_state = GameState.start()
        controller = ScreenController(mock_serial)
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"e,0.0,0  0;")]
        mock_serial.reset_mock()

        # Basic tick
        game_state = game_state.increment_combo(KeyCode.from_char("a"))
        controller = ScreenController(mock_serial)
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"c,1.0,1;")]
        mock_serial.reset_mock()

        controller.tick(game_state)
        # Nothing changed so nothing called
        assert mock_serial.write.call_args_list == []
        mock_serial.reset_mock()

        # Second tick
        game_state = game_state.increment_combo(KeyCode.from_char("a"))
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"c,1.0,2;")]


def test_mode_change():
    mock_serial = Mock()
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        # Start
        game_state = GameState.start()
        controller = ScreenController(mock_serial)
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"e,0.0,0  0;")]
        mock_serial.reset_mock()
        frozen_time.tick(delta=timedelta(seconds=0.5))
        game_state = game_state.copy(
            current_combo=999, recorded_wpms=[0, 100, 1000], time_of_last_key=time()
        )
        frozen_time.tick(delta=timedelta(seconds=1))
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"c,0.9,999;")]
        mock_serial.reset_mock()
        frozen_time.tick(delta=timedelta(seconds=controller.MODE_CHANGE_TIME + 1))
        game_state = game_state.copy(
            time_of_last_key=time()
        )  # make sure we dont timeout
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"w,1.0,100;")]


def test_count_down():
    mock_serial = Mock()
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        # Start
        game_state = GameState.start()
        controller = ScreenController(mock_serial)
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"e,0.0,0  0;")]
        mock_serial.reset_mock()
        frozen_time.tick(delta=timedelta(seconds=1))
        game_state = game_state.copy(
            current_combo=999,
            recorded_wpms=[0, 100, 1000],
            time_of_last_key=time(),
            max_combo=1000,
            max_median_wpm=80,
        )
        frozen_time.tick(delta=timedelta(seconds=3))
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"w,0.7,100;")]
        mock_serial.reset_mock()

        frozen_time.tick(delta=timedelta(seconds=3))
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"c,0.4,999;")]
        mock_serial.reset_mock()

        frozen_time.tick(delta=timedelta(seconds=3))
        controller.tick(game_state)
        assert mock_serial.write.call_args_list == [call(b"w,0.1,100;")]
        mock_serial.reset_mock()

        frozen_time.tick(delta=timedelta(seconds=3))
        controller.tick(game_state.combo_stopped())
        assert mock_serial.write.call_args_list == [call(b"e,0.0,1000  80;")]
        mock_serial.reset_mock()
