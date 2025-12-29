# Controller Application

Handheld controller firmware for ESP32-C3.

## Files

- `boot.py` - Minimal boot script, sets up sys.path to include lib/
- `main.py` - Main application logic (pairing and normal mode)
- `hardware.py` - GPIO pin configuration for controller

## Hardware

- Potentiometer on GPIO0 (speed control)
- Direction button on GPIO1 (toggle + pairing trigger)
- Status LED on GPIO2 (direction indicator)
- 2xAA battery power

## Operation Modes

1. **Pairing Mode**: Hold button during power-on to pair with a train
2. **Normal Mode**: Standard operation, sends control messages at 20Hz
