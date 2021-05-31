from typing import cast
from unittest.mock import Mock, call, patch

import pytest
from pynput.keyboard import KeyCode

from power_mode.main import GameState, StripController


@pytest.fixture
def strip_controller() -> StripController:
    with patch(
        "power_mode.main.sleep",
    ):
        yield StripController(Mock())


def test_tick(strip_controller: StripController):
    mock_serial = cast(Mock, strip_controller.serial_connection)
    strip_controller.index = 100
    strip_controller.color = 5
    game_state = GameState.start().copy(current_combo=5)

    strip_controller.tick(game_state)

    # Tick should not change anything if the state has a combo
    assert strip_controller.index == 100
    assert strip_controller.color == 5

    game_state = game_state.combo_stopped()
    strip_controller.tick(game_state)

    assert strip_controller.index == 0
    assert strip_controller.color != 5
    assert mock_serial.write.call_args_list == [call(b"0,e;")]

    for _ in range(0, 5):
        strip_controller.tick(game_state)
        assert strip_controller.index == 0
        assert strip_controller.color != 5

    # Despite calling it several times we only actually wrote to serial once
    assert mock_serial.write.call_args_list == [call(b"0,e;")]


def test_key_down(strip_controller: StripController):
    game_state = GameState.start()
    mock_serial = cast(Mock, strip_controller.serial_connection)
    for index in range(StripController.NUM_PIXELS):
        strip_controller.key_down(KeyCode.from_char("a"), game_state)
        assert len(mock_serial.write.call_args_list) == index + 1
        assert mock_serial.write.call_args == call(f"{index},0;".encode("utf-8"))
    # Next call should change the color
    strip_controller.key_down(KeyCode.from_char("a"), game_state)
    assert len(mock_serial.write.call_args_list) == StripController.NUM_PIXELS + 1
    current_color = strip_controller.color
    assert current_color != 0
    assert mock_serial.write.call_args == call(f"0,{current_color};".encode("utf-8"))


def test_colors(strip_controller: StripController):
    game_state = GameState.start()
    mock_serial = cast(Mock, strip_controller.serial_connection)
    colors = []
    for _ in range(100):
        colors.append(strip_controller.color)
        for _ in range(StripController.NUM_PIXELS + 1):
            strip_controller.key_down(KeyCode.from_char("a"), game_state)

    last_color = -1
    for color in colors:
        assert last_color != color
        last_color = color
