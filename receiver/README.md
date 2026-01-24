# Receiver Application

Train receiver firmware for ESP32-C3.

## Files

- `boot.py` - Minimal boot script, sets up sys.path to include lib/
- `main.py` - Main application logic (pairing and normal mode)

GPIO pin assignments are centralized in [lib/hardware.py](../lib/hardware.py).

## Hardware

- **Motor 1 (TB6612 Channel A):**
  - PWM: GPIO2 (PWMA)
  - IN1: GPIO4 (AIN1)
  - IN2: GPIO3 (AIN2)

- **Motor 2 (TB6612 Channel B):**
  - PWM: GPIO5 (PWMB)
  - IN1: GPIO7 (BIN1)
  - IN2: GPIO6 (BIN2)

- **Other I/O:**
  - Status LED: GPIO8 (status indicator, active high)
  - Pairing button: GPIO10 (external button, active low with pull-up)

- **Power:**
  - 2S LiPo battery (7.4V nominal) with USB-C charging via BMS
  - MP1584EN buck converter: Battery → 5V → ESP32 VIN pin
  - **Important:** Add 100-470µF bulk capacitor on motor driver power input

See main README.md for detailed GPIO assignments, motor driver wiring, and power system design.

## Operation Modes

1. **Pairing Mode**: Hold button during power-on to pair with a controller
2. **Normal Mode**: Receives control messages and drives motors with 125ms safety timeout
