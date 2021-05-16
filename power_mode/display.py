import threading
from time import time

from pynput import keyboard
import serial
from serial.tools import list_ports


def send_state(controller):
    threading.Timer(.1, send_state, args=[controller]).start()
    controller.send()


class Controller:
    def __init__(self, serial_connection):
        self.combo = 0
        self.combo_timeout = 10
        self.time_at_last_key = time()
        self.serial_connection = serial_connection

    def key_down(self, key):
        self.combo += 1
        self.time_at_last_key = time()

    def send(self):
        time_left = self.percent_time_left
        if not time_left:
            self.combo = 0
        msg = f"{time_left},{self.combo};".encode('utf-8')
        self.serial_connection.write(msg)

    @property
    def percent_time_left(self):
        seconds_past = time() - self.time_at_last_key
        time_left = (self.combo_timeout - seconds_past) / self.combo_timeout
        return time_left if time_left >= 0 else 0


def main():
    metros = list(list_ports.grep("Adafruit Metro"))
    if len(metros) > 1:
        print(
            f"Multiple metros found. Going with the first {metros[0].description} {metros[0].serial_number}"
        )
    elif not metros:
        print("No metros found!")
    else:
        print("Opening controller port")
        controller = Controller(serial.Serial(metros[0].device, baudrate=9600))
        print("Starting game")
        send_state(controller)
        print("Starting listener")
        with keyboard.Listener(
                on_press=controller.key_down
        ) as listener:
            listener.join()


if __name__ == "__main__":
    main()
