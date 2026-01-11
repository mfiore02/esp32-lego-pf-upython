# README Files Audit Report

**Date:** 2026-01-10
**Scope:** Audit all README and markdown documentation files for accuracy and completeness

---

## Critical Issues Found

### 1. controller/README.md ❌ CRITICAL

**Issues:**
- **Line 13:** GPIO0 → Should be **GPIO1** (Potentiometer)
- **Line 14:** GPIO1 → Should be **GPIO10** (Direction button)
- **Line 15:** GPIO2 → Should be **GPIO8** (Status LED)
- **Line 21:** Says "20Hz" but README.md says "50Hz" (actual is 20Hz from code)
- **Missing:** No mention that hardware.py doesn't exist yet

**Impact:** Users will wire hardware to wrong pins, system will not work

**Correct GPIO Mapping:**
```
- Potentiometer on GPIO1 (speed control, ADC)
- Direction button on GPIO10 (toggle + pairing trigger)
- Status LED on GPIO8 (direction indicator)
- 2x/3xAA battery power (see main README for voltage requirements)
```

---

### 2. receiver/README.md ❌ CRITICAL

**Issues:**
- **Line 13-14:** Motor driver pins completely wrong and incomplete
  - Current: "Motor 1 PWM on GPIO2, Direction on GPIO3"
  - Should be: "Motor 1: PWM=GPIO2, IN1=GPIO3, IN2=GPIO4"
- **Line 14:** Motor 2 completely wrong
  - Current: "Motor 2 PWM on GPIO4, Direction on GPIO5"
  - Should be: "Motor 2: PWM=GPIO5, IN1=GPIO6, IN2=GPIO7"
- **Line 15:** GPIO9 → Should be **GPIO10** (Pairing button)
- **Missing:** No mention of Status LED (GPIO8)
- **Missing:** No mention that hardware.py doesn't exist yet
- **Misleading:** Says "BOOT button" but that's not accurate anymore

**Impact:** Motor wiring will be completely wrong, motors won't work

**Correct GPIO Mapping:**
```
- Motor 1: PWM=GPIO2, IN1=GPIO3, IN2=GPIO4 (TB6612 PWMA, AIN1, AIN2)
- Motor 2: PWM=GPIO5, IN1=GPIO6, IN2=GPIO7 (TB6612 PWMB, BIN1, BIN2)
- Status LED on GPIO8 (status indicator)
- Pairing button on GPIO10 (external button, active low)
- 2S LiPo with USB-C charging via BMS
```

---

### 3. lib/README.md ⚠️ MINOR

**Issues:**
- **Line 7:** Says "NVM configuration storage" but should say "**Filesystem** configuration storage"
- **Description accurate** but terminology outdated after switching from NVS to filesystem

**Fix:**
```markdown
- `config_manager.py` - Versioned filesystem-based configuration storage (JSON)
```

---

### 4. hwil/README.md ❌ MODERATE

**Issues:**
- **Line 9:** Uses `ampy` instead of `mpremote` (wrong tool)
- **Line 19:** File name `test_button.py` → Should be `test_button_hwil.py`
- **Line 20:** File name `test_motors.py` → Should be `test_motor_driver_hwil.py`
- **Line 21:** File name `test_espnow_ping.py` → Should be `test_espnow_protocol_hwil.py`
- **Line 22:** File name `test_led.py` → Should be `test_led_hwil.py`
- **Line 23:** File name `test_potentiometer.py` → Should be `test_potentiometer_hwil.py`
- **Missing:** `test_config_manager_hwil.py`

**Impact:** Users will try to use wrong tool and can't find test files

**Correct Content:**
```markdown
# Hardware-in-Loop Tests

Test scripts designed to be flashed directly to ESP32 devices for validation.

## Usage

Use the deployment script:

```bash
# Windows
.\tools\deploy_hwil.sh COM3

# Linux/Mac
./tools/deploy_hwil.sh /dev/ttyUSB0
```

Or manually with mpremote:

```bash
# Flash a HWIL test to device
mpremote connect /dev/ttyUSB0 fs cp hwil/test_button_hwil.py :main.py

# Monitor serial output
mpremote connect /dev/ttyUSB0 repl
```

## Test Scripts

- `test_button_hwil.py` - Verify button debouncing and detection
- `test_led_hwil.py` - LED pattern validation
- `test_potentiometer_hwil.py` - ADC reading and calibration
- `test_motor_driver_hwil.py` - Test motor control (PWM, direction, safety)
- `test_espnow_protocol_hwil.py` - Two-device communication test
- `test_config_manager_hwil.py` - Filesystem persistence validation

See `tools/deploy_hwil.sh` for automated deployment or `tools/MPREMOTE_GUIDE.md` for manual deployment instructions.
```

---

### 5. tests/README.md ⚠️ MINOR

**Issues:**
- **Missing test files** in documentation:
  - `test_button.py`
  - `test_led.py`
  - `test_motor_driver.py`
- **Line 13-15:** Only lists 3 of 6 test files

**Impact:** Users don't know all available unit tests

**Correct Content:**
```markdown
# Unit Tests

Host-based unit tests for shared library modules.

## Running Tests

```bash
python -m pytest tests/
```

## Test Coverage

- `test_button.py` - Button debouncing and edge detection
- `test_config_manager.py` - Configuration storage and versioning
- `test_espnow_protocol.py` - Message encoding/decoding
- `test_led.py` - LED pattern timing and state management
- `test_motor_driver.py` - Motor control logic and safety
- `test_potentiometer.py` - Dead zone calibration logic

All unit tests run on host Python (no hardware required).
Hardware validation tests are in the `hwil/` directory.
```

---

### 6. tools/README.md ❌ MODERATE

**Issues:**
- **Line 7, 14:** Script names wrong
  - Says `flash_controller.sh` → Should be `deploy_controller.sh`
  - Says `flash_receiver.sh` → Should be `deploy_receiver.sh`
- **Missing:** No mention of `deploy_hwil.sh`
- **Line 35:** Says to install `adafruit-ampy` but we use `mpremote`
- **Missing:** Link to MPREMOTE_GUIDE.md

**Impact:** Users will try to run non-existent scripts

**Correct Content:**
```markdown
# Development Tools

Deployment and configuration utilities.

## Scripts

### deploy_controller.sh
Deploys controller firmware to ESP32-C3.

```bash
# Windows
.\tools\deploy_controller.sh COM3

# Linux/Mac
./tools/deploy_controller.sh /dev/ttyUSB0
```

### deploy_receiver.sh
Deploys receiver firmware to ESP32-C3.

```bash
# Windows
.\tools\deploy_receiver.sh COM3

# Linux/Mac
./tools/deploy_receiver.sh /dev/ttyUSB0
```

### deploy_hwil.sh
Deploys HWIL tests for hardware validation.

```bash
# Windows
.\tools\deploy_hwil.sh COM3

# Linux/Mac
./tools/deploy_hwil.sh /dev/ttyUSB0
```

### cli.py (TODO - Not Yet Implemented)
Serial-based configuration tool for devices.

```bash
python tools/cli.py /dev/ttyUSB0

>>> config.show()
>>> config.unpair()
>>> config.set('pot_calibration.min', 150)
```

## Requirements

```bash
pip install esptool mpremote
```

## Documentation

See [MPREMOTE_GUIDE.md](MPREMOTE_GUIDE.md) for detailed mpremote usage examples.
```

---

## Additional Findings

### 7. Main README.md ✅ MOSTLY CORRECT

**Verified Accurate:**
- GPIO assignments table (lines 96-116) ✅
- Control loop rate 20Hz (line 44, matches code) ✅
  **Note:** Line 21 says "20Hz updates" but this is correct
- Configuration format (lines 117-133) ✅
- Development phases checklist ✅
- File structure ✅

**Minor Issues:**
- **Line 12:** Says "stored in NVS flash" → Should say "stored in filesystem (JSON)"
- **Line 34:** Reference to config_manager as "NVM storage" → Should be "Filesystem storage"

**Recommendations:**
- Consider updating line 12 to reflect filesystem storage
- Line 34 in project structure already says "NVM storage abstraction (versioned)" - update to "Filesystem storage"

---

### 8. docs/NVS_ISSUE.md ✅ ACCURATE

**Status:** Historical document explaining why we chose filesystem over NVS. Content is accurate and useful.

---

### 9. tools/MPREMOTE_GUIDE.md ✅ ACCURATE

**Status:** Comprehensive mpremote guide. Content verified accurate.

**Minor Issue:**
- **Line 93:** References `deploy_hwil_test.bat` which doesn't exist
- **Line 99:** References `deploy_hwil_test.sh` which doesn't exist
  **Actual script:** `deploy_hwil.sh`

---

## Summary

### Files Requiring Updates: 6

1. ❌ **controller/README.md** - All GPIO pins wrong (CRITICAL)
2. ❌ **receiver/README.md** - All GPIO pins wrong (CRITICAL)
3. ❌ **hwil/README.md** - Wrong tool (ampy), wrong filenames
4. ❌ **tests/README.md** - Missing test files
5. ❌ **tools/README.md** - Wrong script names, wrong tool
6. ⚠️  **lib/README.md** - Says NVM instead of filesystem
7. ⚠️  **README.md** (main) - 2 minor NVS→filesystem terminology updates
8. ⚠️  **tools/MPREMOTE_GUIDE.md** - Wrong deployment script name reference

### Verified Accurate: 2

- ✅ **docs/NVS_ISSUE.md** - Correct historical documentation
- ✅ **HWIL_AUDIT_REPORT.md** - Just created, accurate

---

## Priority

**HIGH PRIORITY (Critical - Will Break Hardware):**
1. controller/README.md
2. receiver/README.md

**MEDIUM PRIORITY (Will Confuse Users):**
3. hwil/README.md
4. tools/README.md

**LOW PRIORITY (Terminology/Completeness):**
5. tests/README.md
6. lib/README.md
7. Main README.md (minor)
8. tools/MPREMOTE_GUIDE.md (minor)

---

## Next Steps

1. Fix all critical GPIO mapping errors in controller/receiver READMEs
2. Update tool references (ampy → mpremote, correct script names)
3. Update test file listings
4. Update NVM → filesystem terminology where needed
5. Verify all changes against actual file structure
6. Commit all fixes together
