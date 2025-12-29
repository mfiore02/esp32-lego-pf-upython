# Receiver Application

Train receiver firmware for ESP32-C3.

## Files

- `boot.py` - Minimal boot script, sets up sys.path to include lib/
- `main.py` - Main application logic (pairing and normal mode)
- `hardware.py` - GPIO pin configuration for receiver

## Hardware

- Motor 1 PWM on GPIO2, Direction on GPIO3
- Motor 2 PWM on GPIO4, Direction on GPIO5
- Pairing button on GPIO9 (BOOT button)
- 2S LiPo with USB-C charging

## Operation Modes

1. **Pairing Mode**: Hold button during power-on to pair with a controller
2. **Normal Mode**: Receives control messages and drives motors with 500ms safety timeout
