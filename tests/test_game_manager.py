from datetime import timedelta
from unittest.mock import Mock

import freezegun
from pynput.keyboard import KeyCode

from power_mode.main import GameManager, GameState


def test_key_down():
    mock_controller_one = Mock()
    mock_controller_two = Mock()
    mock_controllers = [mock_controller_one, mock_controller_two]
    with freezegun.freeze_time("2020-05-17 10:12:34"):
        game_manager = GameManager(serial_controllers=mock_controllers)
        game_manager.trigger_key_down(KeyCode.from_char("a"))
        expected_gamestate = GameState(
            current_combo=1,
            max_combo=1,
            max_median_wpm=0,
            combo_at_last_timeout=0,
            median_wpm_at_last_timeout=0,
            combo_timeout=10,
            time_of_last_key=1589710354.0,
            combo_start=1589710354.0,
            recorded_wpms=[],
            num_backspaces=0,
        )

        assert game_manager.game_state == expected_gamestate
        for controller in mock_controllers:
            assert len(controller.tick.call_args_list) == 0
            assert len(controller.key_down.call_args_list) == 1
            args, _ = controller.key_down.call_args_list[0]
            key, state = args
            assert KeyCode.from_char("a") == key
            assert expected_gamestate == state
            # Verify we send a copy of the state
            assert state == game_manager.game_state
            assert id(state) != id(game_manager.game_state)


def test_key_down_multiple():
    mock_controller_one = Mock()
    mock_controller_two = Mock()
    mock_controllers = [mock_controller_one, mock_controller_two]
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        game_manager = GameManager(serial_controllers=mock_controllers)
        for _ in range(30):
            game_manager.trigger_key_down(KeyCode.from_char("a"))
            frozen_time.tick(delta=timedelta(seconds=1))
        expected_gamestate = GameState(
            current_combo=30,
            max_combo=30,
            max_median_wpm=12,
            combo_at_last_timeout=0,
            median_wpm_at_last_timeout=0,
            combo_timeout=10,
            time_of_last_key=1589710383.0,
            combo_start=1589710354.0,
            recorded_wpms=[12, 12],
            num_backspaces=0,
        )
        assert game_manager.game_state == expected_gamestate
        for controller in mock_controllers:
            assert len(controller.key_down.call_args_list) == 30
            assert len(controller.tick.call_args_list) == 0


def test_trigger_tick():
    mock_controller_one = Mock()
    mock_controller_two = Mock()
    mock_controllers = [mock_controller_one, mock_controller_two]
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        starting_gamestate = GameState(
            current_combo=1,
            max_combo=1,
            max_median_wpm=0,
            combo_at_last_timeout=0,
            median_wpm_at_last_timeout=0,
            combo_timeout=10,
            time_of_last_key=1589710354.0,
            combo_start=1589710354.0,
            recorded_wpms=[],
            num_backspaces=0,
        )
        game_manager = GameManager(serial_controllers=mock_controllers)
        game_manager.game_state = starting_gamestate
        game_manager.trigger_tick()
        assert game_manager.game_state == starting_gamestate
        for controller in mock_controllers:
            assert len(controller.key_down.call_args_list) == 0
            assert len(controller.tick.call_args_list) == 1
            args, _ = controller.tick.call_args_list[0]
            state = args[0]
            # Nothing happened that changes state so i expected it to be the same
            assert starting_gamestate == state
            # Verify we send a copy of the state
            assert state == game_manager.game_state
            assert id(state) != id(game_manager.game_state)
        for controller in mock_controllers:
            controller.reset_mock()
        frozen_time.tick(
            delta=timedelta(seconds=game_manager.game_state.combo_timeout + 1)
        )
        game_manager.trigger_tick()

        expected_gamestate = GameState(
            current_combo=0,
            max_combo=1,
            max_median_wpm=0,
            combo_at_last_timeout=1,
            median_wpm_at_last_timeout=0,
            combo_timeout=10,
            time_of_last_key=1589710354.0,
            combo_start=1589710365.0,
            recorded_wpms=[],
            num_backspaces=0,
        )
        assert game_manager.game_state == expected_gamestate
        for controller in mock_controllers:
            assert len(controller.key_down.call_args_list) == 0
            assert len(controller.tick.call_args_list) == 1
            args, _ = controller.tick.call_args_list[0]
            state = args[0]
            # Nothing happened that changes state so i expected it to be the same
            assert expected_gamestate == state
            # Verify we send a copy of the state
            assert state == game_manager.game_state
            assert id(state) != id(game_manager.game_state)
