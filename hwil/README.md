# Hardware-in-Loop Tests

Test scripts designed to be flashed directly to ESP32 devices for validation.

## Usage

```bash
# Flash a HWIL test to device
ampy --port /dev/ttyUSB0 put hwil/test_button.py main.py

# Monitor serial output
screen /dev/ttyUSB0 115200
# or
python -m serial.tools.miniterm /dev/ttyUSB0 115200
```

## Test Scripts

- `test_button.py` - Verify button debouncing and detection
- `test_motors.py` - Test motor control (PWM, direction, safety)
- `test_espnow_ping.py` - Two-device communication test
- `test_led.py` - LED pattern validation
- `test_potentiometer.py` - ADC reading and calibration

Each test script is standalone and prints results to the serial console.
