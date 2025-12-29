# Unit Tests

Host-based unit tests for shared library modules.

## Running Tests

```bash
python -m pytest tests/
```

## Test Coverage

- `test_config_manager.py` - Configuration storage and versioning
- `test_espnow_protocol.py` - Message encoding/decoding
- `test_potentiometer.py` - Dead zone calibration logic

Note: Tests that require hardware are in the `hwil/` directory.
