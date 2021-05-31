from __future__ import annotations

import math
import random
import statistics
import threading
from abc import ABC
from dataclasses import dataclass
from time import sleep, time
from typing import List, Optional, Type, TypeVar

import serial
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from serial import Serial
from serial.tools import list_ports

T = TypeVar("T")


@dataclass
class GameState:
    CHARS_IN_WORD = 5
    MIN_WORDS_FOR_WPM = 5

    current_combo: int
    max_combo: int
    max_median_wpm: int
    combo_at_last_timeout: int
    median_wpm_at_last_timeout: int
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
            max_median_wpm=0,
            combo_at_last_timeout=0,
            median_wpm_at_last_timeout=0,
            combo_timeout=10,
            time_of_last_key=time() - 10,  # want to start 'timed out'
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
        ) / GameState.CHARS_IN_WORD
        if words_typed < GameState.MIN_WORDS_FOR_WPM:
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

    @staticmethod
    def _new_if_exists(new: Optional[T], original: T) -> T:
        return original if new is None else new

    def copy(
        self,
        current_combo: Optional[int] = None,
        max_combo: Optional[int] = None,
        max_median_wpm: Optional[int] = None,
        combo_at_last_timeout: Optional[int] = None,
        median_wpm_at_last_timeout: Optional[int] = None,
        combo_timeout: Optional[int] = None,
        time_of_last_key: Optional[float] = None,
        combo_start: Optional[float] = None,
        recorded_wpms: Optional[List[int]] = None,
        num_backspaces: Optional[int] = None,
    ) -> GameState:
        return GameState(
            current_combo=self._new_if_exists(current_combo, self.current_combo),
            max_combo=self._new_if_exists(max_combo, self.max_combo),
            max_median_wpm=self._new_if_exists(max_median_wpm, self.max_median_wpm),
            combo_at_last_timeout=self._new_if_exists(
                combo_at_last_timeout, self.combo_at_last_timeout
            ),
            median_wpm_at_last_timeout=self._new_if_exists(
                median_wpm_at_last_timeout, self.median_wpm_at_last_timeout
            ),
            combo_timeout=self._new_if_exists(combo_timeout, self.combo_timeout),
            time_of_last_key=self._new_if_exists(
                time_of_last_key, self.time_of_last_key
            ),
            combo_start=self._new_if_exists(combo_start, self.combo_start),
            recorded_wpms=self._new_if_exists(recorded_wpms, self.recorded_wpms),
            num_backspaces=self._new_if_exists(num_backspaces, self.num_backspaces),
        )

    def increment_combo(self, key: KeyCode) -> GameState:
        new_combo = self.current_combo + 1
        return self.copy(
            current_combo=new_combo,
            num_backspaces=self.num_backspaces + 1 if key == Key.backspace else None,
            time_of_last_key=time(),
            recorded_wpms=[] if self.current_combo == 0 else None,
            max_combo=new_combo if self.max_combo < new_combo else self.max_combo,
        )

    def combo_stopped(self) -> GameState:
        return self.copy(
            current_combo=0,
            num_backspaces=0,
            combo_start=time(),
            combo_at_last_timeout=self.current_combo
            if self.current_combo
            else self.combo_at_last_timeout,
            median_wpm_at_last_timeout=self.median_wpm
            if self.median_wpm
            else self.median_wpm_at_last_timeout,
            recorded_wpms=[],
        )

    def record_wpm(self) -> GameState:
        current_wpm = self.current_wpm
        recorded_wpms = None
        if current_wpm:
            recorded_wpms = self.recorded_wpms + [current_wpm]
            if len(recorded_wpms) > 100:
                recorded_wpms = recorded_wpms[1:]
        return self.copy(
            recorded_wpms=recorded_wpms,
            max_median_wpm=self.median_wpm
            if self.median_wpm > self.max_median_wpm
            else self.max_median_wpm,
        )


class Controller(ABC):
    def tick(self, state: GameState) -> None:
        raise NotImplementedError()

    def key_down(self, key, state: GameState) -> None:
        raise NotImplementedError()


class SerialOutputController(Controller, ABC):
    def __init__(self, serial_connection: Serial):
        self.serial_connection = serial_connection


class ScreenController(SerialOutputController):
    MODE_CHANGE_TIME = 2

    def __init__(self, serial_connection: Serial):
        super().__init__(serial_connection)
        self.last_mode_change = time()
        self.display_combo = True
        self.last_message = ""

    def key_down(self, _, state: GameState) -> None:
        pass

    def tick(self, state: GameState) -> None:
        cur_time = time()
        self._check_for_mode_change(cur_time)
        self._write_state(state, cur_time)

    def _check_for_mode_change(self, cur_time: float) -> None:
        if cur_time - self.last_mode_change > self.MODE_CHANGE_TIME:
            self.display_combo = not self.display_combo
            self.last_mode_change = cur_time

    def _write_state(self, state: GameState, cur_time: float) -> None:
        """
        Protocol is mode,timeleft,value;
        mode: (one of: c,w,e)
        timeleft: float
        value: some string, should not be longer than 8 chars or so....

        Example:
            c,.5,1039;
        """
        if state.current_combo:
            mode = "c" if self.display_combo or not state.median_wpm else "w"
            value_to_display = (
                str(state.current_combo) if mode == "c" else str(state.median_wpm)
            )
        else:
            mode = "e"
            value_to_display = f"{state.max_combo}  {state.max_median_wpm}"
        truncated_percent_left = "{:.1f}".format(state.percent_time_left)
        msg = f"{mode},{truncated_percent_left},{value_to_display};"
        if msg != self.last_message:
            self.serial_connection.write(msg.encode("utf-8"))
            self.last_message = msg
        self.last_write = cur_time


class BellController(SerialOutputController):
    def __init__(self, serial_connection: Serial):
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
        """
        protocol is just on or off for each of the bell relays
        example: 1010

        Any bell that was triggered over .1 seconds ago is flipped to 0
        """
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


class StripController(SerialOutputController):
    NUM_COLORS = 8
    NUM_PIXELS = 144

    def __init__(self, serial_connection: Serial):
        super().__init__(serial_connection)
        self.colors = []
        self.color = 0
        self.index = 0
        self.last_message = ""
        self._reset_colors()

    def tick(self, state: GameState) -> None:
        if not state.current_combo:
            self.color = 0
            self.index = 0
            self._write_msg("e")

    def key_down(self, key, state: GameState) -> None:
        self._write_msg(str(self.color))
        self.index += 1
        if self.index >= self.NUM_PIXELS:
            self._change_color()

    def _write_msg(self, mode_param: str):
        message = f"{self.index},{mode_param};"
        if message != self.last_message:
            self.serial_connection.write(message.encode("utf-8"))
            self.last_message = message
            # The code driving the pixel strip can screw up serial communication
            # This sleep gives the strip time to draw before we attempt to write another message
            sleep(0.01)

    def _change_color(self):
        if not self.colors:
            self._reset_colors()
        self.index = 0
        self.color = self.colors.pop()

    def _reset_colors(self):
        self.colors = list(range(0, self.NUM_COLORS))
        random.shuffle(self.colors)
        if self.colors[-1] == self.color:
            first_color = self.colors.pop()
            self.colors.insert(0, first_color)


class GameManager:
    def __init__(self, serial_controllers: List[SerialOutputController]):
        self.game_state: GameState = GameState.start()
        self.serial_controllers: List[SerialOutputController] = serial_controllers

    def trigger_tick(self) -> None:
        if self.game_state.percent_time_left == 0:
            self.game_state = self.game_state.combo_stopped()

        snapshot = self.game_state.copy()
        for controller in self.serial_controllers:
            controller.tick(snapshot)

    def trigger_key_down(self, key) -> None:
        self.game_state = self.game_state.increment_combo(key)
        if (
            self.game_state.current_wpm
            and self.game_state.current_combo % self.game_state.CHARS_IN_WORD == 0
        ):
            self.game_state = self.game_state.record_wpm()
        snapshot = self.game_state.copy()
        for controller in self.serial_controllers:
            controller.key_down(key, snapshot)


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


def _game_tick(manager: GameManager):
    manager.trigger_tick()
    threading.Timer(0.05, _game_tick, args=[manager]).start()


def _main():
    print("Starting game")
    game_manager = GameManager(
        serial_controllers=[
            controller
            for controller in [
                _get_controller("Adafruit Metro", ScreenController),
                _get_controller("Arduino Uno", BellController),
                _get_controller("IOUSBHostDevice", StripController),
            ]
            if controller
        ],
    )
    print("Starting listener")
    _game_tick(game_manager)
    with keyboard.Listener(on_press=game_manager.trigger_key_down) as listener:
        listener.join()


if __name__ == "__main__":
    _main()
