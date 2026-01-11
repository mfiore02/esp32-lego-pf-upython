# Hardware-in-Loop Tests

Test scripts designed to be flashed directly to ESP32 devices for validation.

## Usage

Use the deployment script (easiest):

```bash
# Windows
.\tools\deploy_hwil.sh COM3

# Linux/Mac
./tools/deploy_hwil.sh /dev/ttyUSB0
```

Or manually with mpremote:

```bash
# Flash a HWIL test to device as main.py
mpremote connect /dev/ttyUSB0 fs cp hwil/test_button_hwil.py :main.py
mpremote connect /dev/ttyUSB0 fs cp lib/button.py :/lib/button.py

# Monitor serial output
mpremote connect /dev/ttyUSB0 repl
```

## Test Scripts

- `test_button_hwil.py` - Verify button debouncing and edge detection
- `test_led_hwil.py` - LED pattern timing validation
- `test_potentiometer_hwil.py` - ADC reading and calibration helper
- `test_motor_driver_hwil.py` - Test motor control (PWM, direction, reversal)
- `test_espnow_protocol_hwil.py` - Two-device communication test (pairing, ping/pong)
- `test_config_manager_hwil.py` - Filesystem persistence validation across reboots

Each test script is standalone and prints results to the serial console.

## Documentation

- See `tools/deploy_hwil.sh` for automated deployment script
- See `tools/MPREMOTE_GUIDE.md` for detailed mpremote usage examples
- See `HWIL_AUDIT_REPORT.md` for GPIO mapping verification and test coverage analysis
