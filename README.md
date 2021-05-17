# Hardware Powermode

This repository contains the code required to run a hardware 
implementation of editors 'POWER MODE'


When the program starts up it looks for a number of arduinos and hooks them
up as controller. It then sets up two 'events': Key down, and tick.

When either of these events happen the internal game state updates, and the event
along with the current state is passed to any active controllers.

Controllers communicate with hardware over a serial connection. 
Protocol is documented in functions that send data over it


## Hardware

- Ardunio uno hooked up to four 12v relays aimed at some bells

- Adafruit Metro M4 connected to a 64x32 RGB LED Matrix - 3mm pitch  
  (The controller code is very specific to this hardware)