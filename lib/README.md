# Shared Library Modules

This directory contains MicroPython modules shared between the controller and receiver devices.

## Modules

- `config_manager.py` - Versioned filesystem-based configuration storage (JSON)
- `button.py` - Debounced button input driver
- `led.py` - LED pattern control (solid, blink, pulse)
- `potentiometer.py` - ADC reading with dead zone calibration
- `motor_driver.py` - TB6612 motor driver abstraction
- `espnow_protocol.py` - ESP-NOW communication protocol wrapper

## Usage

These modules are imported by both controller and receiver applications. They are designed to be hardware-agnostic where possible, with device-specific configuration passed as parameters.

## Configuration Storage

`config_manager.py` uses filesystem storage (`/config/*.json`) instead of NVS for better debuggability and human-readable configuration. See `docs/NVS_ISSUE.md` for background on this decision.
