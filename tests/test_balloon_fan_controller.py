from unittest.mock import Mock, call

from pynput.keyboard import KeyCode

from power_mode.main import BalloonFanController, GameState


def test_tick():
    mock_serial = Mock()
    controller = BalloonFanController(mock_serial)
    gamestate = GameState.start()
    controller.tick(gamestate)
    assert mock_serial.write.call_count == 1
    assert mock_serial.write.call_args == call(b"0,0;")

    gamestate = gamestate.increment_combo(KeyCode.from_char("a"))
    controller.tick(gamestate)
    assert mock_serial.write.call_count == 2
    assert mock_serial.write.call_args == call(b"1,0;")

    for _ in range(controller.FAN_THRESHOLD - 2):
        gamestate = gamestate.increment_combo(KeyCode.from_char("a"))
        controller.tick(gamestate)
        # The message is unchanged so nothing sends
        assert mock_serial.write.call_count == 2

    gamestate = gamestate.increment_combo(KeyCode.from_char("a"))
    controller.tick(gamestate)
    assert mock_serial.write.call_count == 3
    assert mock_serial.write.call_args == call(b"1,1;")
    gamestate = gamestate.combo_stopped()
    controller.tick(gamestate)
    assert mock_serial.write.call_count == 4
    assert mock_serial.write.call_args == call(b"0,0;")
