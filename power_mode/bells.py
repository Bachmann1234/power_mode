from pynput import keyboard
import serial
from serial.tools import list_ports

NUM_CLICKYS = 4


class Controller:
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection
        self.keys_down = set()

    def _bucket(self, key):
        try:
            keycode = key.vk
        except AttributeError:
            # The last clicky will be saved for this case
            keycode = NUM_CLICKYS - 1
        return keycode % (NUM_CLICKYS - 1)

    def key_up(self, key):
        if self.serial_connection.is_open:
            cmd = f"0{self._bucket(key)}".encode("utf-8")
            self.serial_connection.write(cmd)
            try:
                self.keys_down.remove(key)
            except KeyError:
                pass

    def key_down(self, key):
        if self.serial_connection.is_open:
            if key not in self.keys_down:
                cmd = f"1{self._bucket(key)}".encode("utf-8")
                self.serial_connection.write(cmd)
                self.keys_down.add(key)


def main():
    arduinos = list(list_ports.grep("Arduino Uno"))

    if len(arduinos) > 1:
        print(
            f"Multiple arduinos found. Going with the first {arduinos[0].description} {arduinos[0].serial_number}"
        )
    elif not arduinos:
        print("No arduino found!")
    else:
        print("Opening controller port")
        controller = Controller(serial.Serial(arduinos[0].device, baudrate=9600))
        print("Starting listener")
        with keyboard.Listener(
            on_press=controller.key_down, on_release=controller.key_up
        ) as listener:
            listener.join()


if __name__ == "__main__":
    main()
