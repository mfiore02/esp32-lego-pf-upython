# HWIL and Unit Test Audit Report

**Date:** 2026-01-10
**Scope:** Review all HWIL tests for correct IO mappings and API coverage

## Reference IO Mappings (from README.md)

### Controller
| Function | GPIO | Notes |
|----------|------|-------|
| Potentiometer (ADC) | GPIO1 | Speed control |
| Status LED | GPIO8 | Status indicator |
| Direction Button | GPIO10 | Toggle direction + pairing mode |

### Receiver
| Function | GPIO | Notes |
|----------|------|-------|
| Motor 1 PWM | GPIO2 | TB6612 PWMA |
| Motor 1 IN1 | GPIO3 | TB6612 AIN1 |
| Motor 1 IN2 | GPIO4 | TB6612 AIN2 |
| Motor 2 PWM | GPIO5 | TB6612 PWMB |
| Motor 2 IN1 | GPIO6 | TB6612 BIN1 |
| Motor 2 IN2 | GPIO7 | TB6612 BIN2 |
| Status LED | GPIO8 | Status indicator |
| Pairing Button | GPIO10 | External button (active low) |

---

## Critical Issues Found

### 1. test_button_hwil.py ❌
**Issues:**
- Line 45: `BUTTON_GPIO = 1` → Should be `GPIO10`
- Line 114: `BUTTON_GPIO = 9` → Should be `GPIO10`

**Impact:** Test will fail to detect button presses on correct pin

**Fix Required:**
```python
# Line 45
BUTTON_GPIO = 10  # Controller/Receiver button

# Line 114
BUTTON_GPIO = 10  # Controller/Receiver button
```

---

### 2. test_led_hwil.py ❌
**Issues:**
- Line 45: `LED_GPIO = 2` → Should be `GPIO8`
- Line 104: `LED_GPIO = 2` → Should be `GPIO8`
- Line 148: `LED_GPIO = 2` → Should be `GPIO8`

**Impact:** LED will not light up on correct pin

**Fix Required:**
```python
# Lines 45, 104, 148
LED_GPIO = 8  # Controller/Receiver status LED
```

---

### 3. test_potentiometer_hwil.py ❌
**Issues:**
- Line 44: `POT_GPIO = 0` → Should be `GPIO1`
- Line 90: `POT_GPIO = 0` → Should be `GPIO1`
- Line 149: `POT_GPIO = 0` → Should be `GPIO1`
- Line 196: `POT_GPIO = 0` → Should be `GPIO1`

**Impact:** ADC will read wrong pin, giving incorrect potentiometer values

**Fix Required:**
```python
# Lines 44, 90, 149, 196
POT_GPIO = 1  # Controller potentiometer
```

---

### 4. test_motor_driver_hwil.py ❌
**Issues:**
- Line 279: `pwm2 = PWM(Pin(4), freq=1000, duty=0)` → Should be `GPIO5`
- Line 280: `in1_2 = Pin(5, Pin.OUT)` → Should be `GPIO6`
- Line 281: `in2_2 = Pin(6, Pin.OUT)` → Should be `GPIO7`

**Impact:** Motor 2 will not work correctly in interactive test

**Fix Required:**
```python
# test_interactive() function starting line 259
# Motor 2: PWM=GPIO5, IN1=GPIO6, IN2=GPIO7
pwm2 = PWM(Pin(5), freq=1000, duty=0)
in1_2 = Pin(6, Pin.OUT)
in2_2 = Pin(7, Pin.OUT)
```

**Note:** Other test functions in this file are correct!

---

### 5. test_espnow_protocol_hwil.py ✅
**Status:** No IO issues - uses WiFi only

---

### 6. test_config_manager_hwil.py ✅
**Status:** No IO issues - filesystem only

---

## API Coverage Analysis

### Button Module
**Public APIs:**
- `__init__(pin, active_low, debounce_ms)` ✅ Tested
- `update()` ✅ Tested
- `is_pressed()` ✅ Tested
- `was_pressed()` ✅ Tested
- `was_released()` ✅ Tested
- `press_duration()` ✅ Tested
- `last_press_duration()` ✅ Tested

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ✅ Complete (needs IO fix)

---

### LED Module
**Public APIs:**
- `__init__(pin, active_high)` ✅ Tested
- `set_pattern(pattern)` ✅ Tested
- `update()` ✅ Tested
- `get_pattern()` ✅ Tested
- `is_on()` ✅ Tested
- `turn_on()` ✅ Tested
- `turn_off()` ✅ Tested

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ✅ Complete (needs IO fix)

---

### Potentiometer Module
**Public APIs:**
- `__init__(adc, min_val, max_val, zero_band)` ✅ Tested
- `read()` ✅ Tested
- `read_raw()` ✅ Tested
- `set_calibration(min_val, max_val, zero_band)` ✅ Tested
- `get_calibration()` ✅ Tested

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ✅ Complete (needs IO fix)

---

### Motor Driver Module
**Public APIs (MotorDriver):**
- `__init__(pwm, in1_pin, in2_pin, reverse, deadband)` ✅ Tested
- `drive(speed, mode)` ✅ Tested
- `stop(brake)` ✅ Tested
- `get_speed()` ⚠️  Not tested in HWIL
- `get_pwm()` ⚠️  Not tested in HWIL
- `get_mode()` ⚠️  Not tested in HWIL
- `set_reverse(reverse)` ✅ Tested
- `set_deadband(deadband)` ⚠️  Not tested in HWIL

**Public APIs (DualMotorDriver):**
- `__init__(motor1, motor2)` ✅ Tested
- `drive_both(speed, mode)` ✅ Tested
- `drive_independent(speed1, mode1, speed2, mode2)` ✅ Tested
- `stop_both(brake)` ✅ Tested

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ⚠️  Missing getter/setter tests (low priority - covered in unit tests)

---

### ConfigManager Module
**Public APIs:**
- `__init__(device_type)` ✅ Tested
- `load()` ✅ Tested (implicit)
- `save()` ✅ Tested
- `get(key, default)` ✅ Tested
- `set(key, value)` ✅ Tested
- `reset()` ⚠️  Not tested in HWIL
- `erase()` ✅ Tested
- `get_all()` ⚠️  Not tested in HWIL

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ⚠️  Missing reset/get_all tests (low priority)

---

### ESPNow Protocol Module
**Public APIs:**
- `__init__(device_type)` ✅ Tested
- `init()` ✅ Tested
- `get_mac_address()` ✅ Tested (via get_mac_address_str)
- `get_mac_address_str()` ✅ Tested
- `add_peer(peer_mac)` ✅ Tested
- `remove_peer(peer_mac)` ⚠️  Not tested in HWIL
- `send_control(speed, direction)` ✅ Tested
- `send_ping()` ✅ Tested
- `send_pong()` ✅ Tested
- `send_pair_request()` ✅ Tested
- `send_pair_ack(peer_mac)` ✅ Tested
- `receive(timeout_ms)` ✅ Tested
- `deinit()` ⚠️  Not tested in HWIL

**Unit Test Coverage:** ✅ Complete
**HWIL Coverage:** ⚠️  Missing remove_peer/deinit tests (low priority)

---

## Summary

### Critical Fixes Required (4)
1. ❌ **test_button_hwil.py** - Wrong GPIO (1/9 instead of 10)
2. ❌ **test_led_hwil.py** - Wrong GPIO (2 instead of 8)
3. ❌ **test_potentiometer_hwil.py** - Wrong GPIO (0 instead of 1)
4. ❌ **test_motor_driver_hwil.py** - Motor 2 pins wrong in interactive test

### Optional Enhancements (Low Priority)
- Add getter method tests to motor driver HWIL
- Add reset()/get_all() tests to config manager HWIL
- Add remove_peer()/deinit() tests to ESP-NOW HWIL

**Recommendation:** Fix all 4 critical issues immediately. The missing API tests are low priority since they're covered in unit tests and are not core functionality for HWIL validation.

---

## Test Execution Status

### Unit Tests
All unit tests pass with current code (no hardware dependencies).

### HWIL Tests
**Will FAIL on hardware** due to incorrect GPIO mappings until fixes applied.

---

## Next Steps

1. Fix GPIO mappings in all 4 HWIL test files
2. Run HWIL tests on hardware to verify fixes
3. Update deployment scripts if needed
4. Consider adding optional API coverage tests (low priority)
