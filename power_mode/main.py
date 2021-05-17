from __future__ import annotations

import math
import statistics
import threading
from abc import ABC
from dataclasses import dataclass
from time import time
from typing import Optional, Type, List

from pynput import keyboard  # type: ignore
import serial  # type: ignore
from pynput.keyboard import Key
from serial.tools import list_ports  # type: ignore


@dataclass
class GameState:
    current_combo: int
    max_combo: int
    combo_timeout: int
    time_of_last_key: float
    combo_start: float
    recorded_wpms: List[int]
    num_backspaces: int

    @staticmethod
    def start() -> GameState:
        return GameState(
            current_combo=0,
            max_combo=0,
            combo_timeout=10,
            time_of_last_key=time() - 10,
            combo_start=time(),
            recorded_wpms=[],
            num_backspaces=0,
        )

    @property
    def percent_time_left(self) -> float:
        seconds_past = time() - self.time_of_last_key
        time_left = (self.combo_timeout - seconds_past) / self.combo_timeout
        return time_left if time_left >= 0 else 0

    @property
    def current_wpm(self) -> int:
        words_typed = (
            self.current_combo - self.num_backspaces
        ) / 5  # WPM defines a word as 5 chars
        if words_typed < 5:
            return 0
        minutes_passed = (time() - self.combo_start) / 60
        return math.floor(words_typed / minutes_passed)

    @property
    def median_wpm(self) -> int:
        return (
            math.floor(statistics.median(self.recorded_wpms))
            if self.recorded_wpms
            else 0
        )

    def copy(self) -> GameState:
        return GameState(
            current_combo=self.current_combo,
            max_combo=self.max_combo,
            combo_timeout=self.combo_timeout,
            time_of_last_key=self.time_of_last_key,
            combo_start=self.combo_start,
            recorded_wpms=self.recorded_wpms,
            num_backspaces=self.num_backspaces,
        )

    def increment_combo(self, key) -> GameState:
        self.current_combo += 1
        self.time_of_last_key = time()
        if key == Key.backspace:
            self.num_backspaces += 1
        if self.current_combo == 1:
            self.recorded_wpms = []
        return self.copy()

    def combo_stopped(self) -> GameState:
        if self.current_combo > self.max_combo:
            self.max_combo = self.current_combo
        self.current_combo = 0
        self.num_backspaces = 0
        self.combo_start = time()
        return self.copy()

    def record_wpm(self) -> GameState:
        current_wpm = self.current_wpm
        if current_wpm:
            self.recorded_wpms.append(current_wpm)
            if len(self.recorded_wpms) > 100:
                self.recorded_wpms = self.recorded_wpms[1:]
        return self.copy()


class Controller(ABC):
    def tick(self, state: GameState) -> None:
        raise NotImplementedError()

    def key_down(self, key, state: GameState) -> None:
        raise NotImplementedError()


class SerialOutputController(Controller, ABC):
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection


class ScreenController(SerialOutputController):
    def __init__(self, serial_connection):
        super().__init__(serial_connection)
        self.last_write = time()
        self.last_mode_change = time()
        self.display_combo = True
        self.last_message = ""

    def key_down(self, _, state: GameState) -> None:
        pass

    def tick(self, state: GameState) -> None:
        cur_time = time()
        self.check_for_mode_change(cur_time)
        if cur_time - self.last_write > 0.1:
            self.write_state(state, cur_time)

    def check_for_mode_change(self, cur_time: float) -> None:
        if cur_time - self.last_mode_change > 2:
            self.display_combo = not self.display_combo
            self.last_mode_change = cur_time

    def write_state(self, state: GameState, cur_time: float) -> None:
        if state.current_combo:
            mode = "c" if self.display_combo else "w"
            value_to_display = (
                str(state.current_combo)
                if self.display_combo
                else str(state.median_wpm)
            )
        else:
            mode = "e"
            value_to_display = f"{state.max_combo} {state.median_wpm}"
        msg = f"{mode},{state.percent_time_left},{value_to_display};"
        if msg != self.last_message:
            self.serial_connection.write(msg.encode("utf-8"))
            self.last_message = msg
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
        serial_controllers: List[SerialOutputController],
    ):
        self.game_state = GameState.start()
        self.serial_controllers: List[SerialOutputController] = serial_controllers

    def trigger_tick(self) -> None:
        if self.game_state.percent_time_left == 0:
            self.game_state = self.game_state.combo_stopped()

        snapshot = self.game_state.copy()
        for controller in self.serial_controllers:
            controller.tick(snapshot)
        threading.Timer(0.05, self.trigger_tick).start()

    def key_down(self, key) -> None:
        self.game_state = self.game_state.increment_combo(key).record_wpm()
        snapshot = self.game_state.copy()
        for controller in self.serial_controllers:
            controller.key_down(key, snapshot)


def main():
    print("Starting game")
    game_manager = GameManager(
        serial_controllers=[
            controller
            for controller in [
                _get_controller("Adafruit Metro", ScreenController),
                _get_controller("Arduino Uno", BellController),
            ]
            if controller
        ],
    )
    # Begin the loop. Trigger tick will trigger itself going forward
    game_manager.trigger_tick()
    print("Starting listener")
    with keyboard.Listener(on_press=game_manager.key_down) as listener:
        listener.join()


if __name__ == "__main__":
    main()
