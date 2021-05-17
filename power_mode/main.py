from __future__ import annotations
import threading
from abc import ABC
from dataclasses import dataclass
from time import time
from typing import Optional, Type, List

from pynput import keyboard  # type: ignore
import serial  # type: ignore
from serial.tools import list_ports  # type: ignore


@dataclass
class GameState:
    combo_count: int
    combo_timeout: int
    time_of_last_key: float
    combo_start: float

    def percent_time_left(self) -> float:
        seconds_past = time() - self.time_of_last_key
        time_left = (self.combo_timeout - seconds_past) / self.combo_timeout
        return time_left if time_left >= 0 else 0

    def copy(self) -> GameState:
        return GameState(
            combo_count=self.combo_count,
            combo_timeout=self.combo_timeout,
            time_of_last_key=self.time_of_last_key,
            combo_start=self.combo_start,
        )


class Controller(ABC):
    def tick(self, state: GameState) -> None:
        raise NotImplementedError()

    def key_down(self, key, state: GameState) -> None:
        raise NotImplementedError()


class GameStateController(Controller):
    def __init__(self):
        self.game_state = GameState(0, 10, time(), time())

    def tick(self, state: GameState) -> None:
        if self.game_state.percent_time_left() == 0:
            self.game_state = GameState(
                combo_count=0,
                combo_timeout=self.game_state.combo_timeout,
                time_of_last_key=time(),
                combo_start=time(),
            )

    def key_down(self, key, state: GameState) -> None:
        self.game_state = GameState(
            combo_count=self.game_state.combo_count + 1,
            combo_timeout=self.game_state.combo_timeout,
            time_of_last_key=time(),
            combo_start=self.game_state.combo_start,
        )

    def get_game_state(self) -> GameState:
        return self.game_state.copy()


class SerialOutputController(Controller, ABC):
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection


class ScreenController(SerialOutputController):
    def __init__(self, serial_connection):
        super().__init__(serial_connection)
        self.last_write = time()

    def key_down(self, _, state: GameState) -> None:
        pass

    def tick(self, state: GameState) -> None:
        time_left = state.percent_time_left()
        msg = f"{time_left},{state.combo_count};".encode("utf-8")
        cur_time = time()
        if cur_time - self.last_write > 0.1:
            self.serial_connection.write(msg)
            self.last_write = cur_time


class BellController(SerialOutputController):
    def __init__(self, serial_connection):
        super().__init__(serial_connection)
        self.bell_click_times = [1.0, 1.0, 1.0, 1.0]
        self.last_message = None
        self.current_index = 0

    def key_down(self, key, state: GameState) -> None:
        self.bell_click_times[self.current_index] = time()
        self._increment_index()
        self._send()

    def tick(self, _: GameState):
        self._send()

    def _increment_index(self):
        self.current_index += 1
        if self.current_index == len(self.bell_click_times):
            self.current_index = 0

    def _send(self):
        curr_time = time()
        msg = "".join(
            [
                "1" if curr_time - bell_clicked_time < 0.1 else "0"
                for bell_clicked_time in self.bell_click_times
            ]
        )
        if msg != self.last_message:
            self.last_message = msg
            self.serial_connection.write(msg.encode("utf-8"))


def _get_controller(
    identifier: str, controller: Type[SerialOutputController]
) -> Optional[SerialOutputController]:
    controllers = list(list_ports.grep(identifier))
    if len(controllers) > 1:
        print(
            f"Multiple controllers with identifier '{identifier}' "
            f"found. Going with the first "
            f"{controllers[0].description} {controllers[0].serial_number}"
        )
    elif not controllers:
        print(f"No {identifier} found!")
        return None
    print(f"Opening {identifier} controller port")
    microcontroller = controller(serial.Serial(controllers[0].device, baudrate=9600))
    return microcontroller


class GameManager:
    def __init__(
        self,
        game_state_controller: GameStateController,
        serial_controllers: List[SerialOutputController],
    ):
        self.game_state_controller = game_state_controller
        self.serial_controllers = serial_controllers

    def trigger_tick(self) -> None:
        self.game_state_controller.tick(self.game_state_controller.get_game_state())
        game_state_snapshot = self.game_state_controller.get_game_state()
        for controller in self.serial_controllers:
            controller.tick(game_state_snapshot)
        threading.Timer(0.05, self.trigger_tick).start()

    def key_down(self, key) -> None:
        self.game_state_controller.key_down(
            key, self.game_state_controller.get_game_state()
        )
        game_state_snapshot = self.game_state_controller.get_game_state()
        for controller in self.serial_controllers:
            controller.key_down(key, game_state_snapshot)


def main():
    print("Starting game")
    game_manager = GameManager(
        game_state_controller=GameStateController(),
        serial_controllers=[
            controller
            for controller in [
                _get_controller("Adafruit Metro", ScreenController),
                _get_controller("Arduino Uno", BellController),
            ]
            if controller
        ],
    )
    game_manager.trigger_tick()
    print("Starting listener")
    with keyboard.Listener(on_press=game_manager.key_down) as listener:
        listener.join()


if __name__ == "__main__":
    main()
