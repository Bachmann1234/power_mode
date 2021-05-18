from datetime import timedelta
from unittest.mock import Mock, call

import freezegun
from pynput.keyboard import KeyCode

from power_mode.main import BellController, GameState


def test_bell_controller():
    mock_serial = Mock()
    controller = BellController(mock_serial)
    gamestate = GameState.start()
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        controller.key_down(KeyCode.from_char("a"), gamestate)
        frozen_time.tick(delta=timedelta(seconds=0.04))
        controller.key_down(KeyCode.from_char("a"), gamestate)
        frozen_time.tick(delta=timedelta(seconds=0.04))
        controller.key_down(KeyCode.from_char("a"), gamestate)
        frozen_time.tick(delta=timedelta(seconds=0.04))
        controller.key_down(KeyCode.from_char("a"), gamestate)
        frozen_time.tick(delta=timedelta(seconds=0.04))
        controller.key_down(KeyCode.from_char("a"), gamestate)
        assert mock_serial.write.call_args_list == [
            call(b"1000"),
            call(b"1100"),
            call(b"1110"),
            call(b"0111"),  # First bell times out
            call(b"1011"),  # second bell times out
        ]


def test_bell_controller_can_handle_many_keys():
    mock_serial = Mock()
    controller = BellController(mock_serial)
    gamestate = GameState.start()
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)

        assert mock_serial.write.call_args_list == [
            call(b"1000"),
            call(b"1100"),
            call(b"1110"),
            call(b"1111"),
        ]  # no time passed so everything is 1. Message stops changning so we stop sending


def test_bell_timeout():
    mock_serial = Mock()
    controller = BellController(mock_serial)
    gamestate = GameState.start()
    with freezegun.freeze_time("2020-05-17 10:12:34") as frozen_time:
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        controller.key_down(KeyCode.from_char("a"), gamestate)
        frozen_time.tick(delta=timedelta(seconds=1))
        controller.tick(gamestate)

        assert mock_serial.write.call_args_list == [
            call(b"1000"),
            call(b"1100"),
            call(b"1110"),
            call(b"1111"),
            call(b"0000"),
        ]
