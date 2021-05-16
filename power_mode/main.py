import threading
from abc import ABC
from time import time
from typing import Optional, Type

from pynput import keyboard
import serial
from serial.tools import list_ports


class Controller(ABC):
    def start(self) -> None:
        raise NotImplementedError()

    def key_down(self, key) -> None:
        raise NotImplementedError()


class SerialController(Controller, ABC):
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection


class MetaController(Controller):
    def __init__(self, controllers):
        self.controllers = controllers

    def start(self) -> None:
        for controller in self.controllers:
            controller.start()

    def key_down(self, key) -> None:
        for controller in self.controllers:
            controller.key_down(key)


class ScreenController(SerialController):
    def __init__(self, serial_connection):
        super().__init__(serial_connection)
        self.combo = 0
        self.combo_timeout = 10
        self.time_at_last_key = time()

    def key_down(self, key) -> None:
        self.combo += 1
        self.time_at_last_key = time()

    def start(self) -> None:
        self._send_state()

    def _send_state(self) -> None:
        threading.Timer(0.1, self._send_state).start()
        self._send()

    def _send(self) -> None:
        time_left = self._get_percent_time_left()
        if not time_left:
            self.combo = 0
        msg = f"{time_left},{self.combo};".encode("utf-8")
        self.serial_connection.write(msg)

    def _get_percent_time_left(self) -> float:
        seconds_past = time() - self.time_at_last_key
        time_left = (self.combo_timeout - seconds_past) / self.combo_timeout
        return time_left if time_left >= 0 else 0


class BellController(SerialController):
    def __init__(self, serial_connection):
        super().__init__(serial_connection)
        self.bells = [False, False, False, False]
        self.current_index = 0

    def start(self) -> None:
        self._send_state()

    def key_down(self, key) -> None:
        self._enable_bell(self.current_index)
        threading.Timer(0.2, self._disable_bell, args=[self.current_index]).start()
        self._increment_index()

    def _disable_bell(self, index):
        self.bells[index] = False
        self._send_state()

    def _enable_bell(self, index):
        self.bells[index] = True
        self._send_state()

    def _increment_index(self):
        self.current_index += 1
        if self.current_index == len(self.bells):
            self.current_index = 0

    def _send_state(self):
        self.serial_connection.write(
            "".join(["1" if bell else "0" for bell in self.bells]).encode("utf-8")
        )


def _get_controller(
    identifier: str, controller: Type[SerialController]
) -> Optional[SerialController]:
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


def main():
    print("Starting game")
    controller = MetaController(
        [
            controller
            for controller in [
                _get_controller("Adafruit Metro", ScreenController),
                _get_controller("Arduino Uno", BellController),
            ]
            if controller
        ]
    )
    controller.start()
    print("Starting listener")
    with keyboard.Listener(on_press=controller.key_down) as listener:
        listener.join()


if __name__ == "__main__":
    main()
