# Controller Application

Handheld controller firmware for ESP32-C3.

## Files

- `boot.py` - Minimal boot script, sets up sys.path to include lib/
- `main.py` - Main application logic (pairing and normal mode)

**Note:** `hardware.py` is planned but not yet implemented. GPIO configuration is currently in main.py.

## Hardware

- Potentiometer on GPIO1 (speed control, ADC)
- Direction button on GPIO10 (toggle + pairing trigger, active low with pull-up)
- Status LED on GPIO8 (direction indicator, active high)
- Power: 3x AA batteries (4.5V recommended) or 2x AA with boost converter to 5V
  - **Do NOT connect batteries directly to 3.3V pin!**
  - Connect to 5V/VIN pin on ESP32-C3

See main README.md for detailed GPIO assignments and hardware requirements.

## Operation Modes

1. **Pairing Mode**: Hold button during power-on to pair with a train
2. **Normal Mode**: Standard operation, sends control messages at 20Hz (50ms interval)
