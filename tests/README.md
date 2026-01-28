# Unit Tests

Host-based unit tests for shared library modules.

## Running Tests

```bash
python -m pytest tests/
```

## Test Coverage

- `test_button.py` - Button debouncing and edge detection logic
- `test_config_manager.py` - Configuration storage, versioning, and migration
- `test_espnow_protocol.py` - Message encoding/decoding and protocol logic
- `test_led.py` - LED pattern timing and state management
- `test_motor_driver.py` - Motor control logic, reversal, and safety features
- `test_potentiometer.py` - Dead zone calibration and ADC value mapping
- `test_battery.py` - Battery voltage conversion, status thresholds, and percentage calculation

All unit tests run on host Python (no hardware required).
Hardware validation tests are in the `hwil/` directory.
