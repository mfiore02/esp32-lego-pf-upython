# ESP32 Lego Power Functions Controller

MicroPython implementation of a wireless Lego Power Functions motor controller system using ESP32-C3 and ESP-NOW.

## Overview

This project implements a low-latency wireless control system for Lego Power Functions motors, consisting of:

- **Handheld Controller**: Potentiometer for speed, button for direction toggle, 2xAA powered
- **Train Receiver**: Dual TB6612 motor driver, 2S LiPo with USB-C charging, fits in 8x4 stud Lego box
- **Communication**: ESP-NOW protocol for <10ms latency
- **Pairing**: Button-based pairing with MAC addresses stored in NVS flash

## System Architecture

```
┌─────────────────────┐                    ┌─────────────────────┐
│  CONTROLLER         │                    │  TRAIN RECEIVER     │
│  (Handheld)         │   ESP-NOW (WiFi)   │  (On Train)         │
├─────────────────────┤◄──────────────────►├─────────────────────┤
│ • Potentiometer     │   20Hz updates     │ • TB6612 Driver     │
│ • Direction Button  │   Low latency      │ • 2x Motors         │
│ • Status LED        │   Paired MAC       │ • Pair Button       │
│ • 2xAA Power        │   filtering        │ • 2S LiPo + BMS     │
└─────────────────────┘                    └─────────────────────┘
```

## Project Structure

```
esp32-lego-pf-upython/
├── lib/                          # Shared modules (both devices)
│   ├── espnow_protocol.py        # ESP-NOW wrapper + message protocol
│   ├── config_manager.py         # NVM storage abstraction (versioned)
│   ├── button.py                 # Debounced button driver
│   ├── led.py                    # LED patterns (solid, blink, etc)
│   ├── motor_driver.py           # TB6612 abstraction
│   └── potentiometer.py          # ADC with dead zone handling
│
├── controller/
│   ├── boot.py                   # Minimal - sets up path
│   ├── main.py                   # Controller app entry point
│   └── hardware.py               # Controller GPIO configuration
│
├── receiver/
│   ├── boot.py                   # Minimal - sets up path
│   ├── main.py                   # Receiver app entry point
│   └── hardware.py               # Receiver GPIO configuration
│
├── tests/                        # Unit tests (run on host)
│   ├── test_espnow_protocol.py
│   ├── test_config_manager.py
│   └── test_potentiometer.py
│
├── hwil/                         # Hardware-in-loop test scripts
│   ├── test_button.py            # Flash to device, test button
│   ├── test_motors.py
│   └── test_espnow_ping.py
│
├── tools/
│   ├── flash_controller.sh       # Deploy to controller
│   ├── flash_receiver.sh         # Deploy to receiver
│   └── cli.py                    # USB-C serial config tool
│
├── docs/
│   └── lego_pf_controller_build_guide.pdf
│
└── README.md
```

## Hardware Requirements

### Train Receiver (Per-unit cost: $26-36)
- ESP32-C3 SuperMini
- TB6612FNG dual H-bridge motor driver
- USB-C 2S BMS (balanced charging)
- 2S LiPo 350mAh (45×15×14mm with balance lead)
- AMS1117-3.3V voltage regulator
- Mini slide switch (SPST, 3A+)
- Momentary pushbutton (or use onboard BOOT button)
- 2x Lego PF extension cables
- Prototype board and wiring

### Handheld Controller (Per-unit cost: $8-15)
- ESP32-C3 SuperMini
- 10K potentiometer (linear, panel mount)
- Knob for potentiometer
- Momentary pushbutton (direction + pairing)
- 2xAA battery holder
- SPST slide switch
- LED + 1K resistor
- Small project enclosure

See `docs/lego_pf_controller_build_guide.pdf` for detailed wiring diagrams and assembly instructions.

## GPIO Assignments

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

## Configuration Format

Configuration is stored in JSON format with versioning:

```json
{
  "version": 1,
  "device_type": "controller",
  "paired": true,
  "train_mac": [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC],
  "pot_calibration": {
    "min": 100,
    "max": 3995,
    "zero_band": 50
  }
}
```

## Development Workflow

This project follows an **incremental, test-driven development** approach:

1. Develop a module with clear interface
2. Write unit tests (where applicable)
3. Create HWIL test script
4. Validate on actual hardware
5. Move to next module

### Development Phases

#### Phase 1: Foundation Modules
1. ✅ `lib/config_manager.py` - NVM storage with versioning
2. ✅ `lib/button.py` - Debounced button input
3. ✅ `lib/led.py` - LED pattern control
4. ✅ `lib/potentiometer.py` - ADC with dead zone calibration
5. ✅ `lib/motor_driver.py` - TB6612 PWM control (hardware validated)

#### Phase 2: Communication Layer
6. ✅ `lib/espnow_protocol.py` - Message protocol and ESP-NOW wrapper (hardware validated)

#### Phase 3: Application Logic
7. ✅ `controller/main.py` - Controller application with pairing and control loop
8. ✅ `receiver/main.py` - Receiver application with motor control and safety timeout
9. ✅ End-to-end hardware validation and pairing flow testing (**SYSTEM WORKING!**)

#### Phase 4: Configuration & Deployment
10. ✅ Deployment scripts (controller, receiver, HWIL)
11. ⬜ `tools/cli.py` - USB-C serial configuration tool (optional)
12. ⬜ Final documentation and build guide updates

## Installation & Deployment

### Prerequisites
```bash
pip install esptool mpremote
```

### Flashing MicroPython Firmware
```bash
# Download ESP32-C3 firmware from micropython.org
# Erase flash
esptool.py --chip esp32c3 erase_flash

# Flash MicroPython
esptool.py --chip esp32c3 write_flash -z 0x0 ESP32_GENERIC_C3-*.bin
```

### Deploying Application Code

**Controller:**
```bash
./tools/flash_controller.sh /dev/ttyUSB0
```

**Receiver:**
```bash
./tools/flash_receiver.sh /dev/ttyUSB0
```

## Usage

### Pairing Procedure
1. Hold pairing button on train while powering on → motors twitch once
2. Hold direction button on controller while powering on → LED blinks rapidly
3. Wait 1-3 seconds → devices pair automatically
4. Train motors twitch twice, controller LED goes solid
5. Both devices reboot into normal mode

### Normal Operation
- **Speed**: Turn potentiometer (CCW=stop, CW=max)
- **Direction**: Press button to toggle forward/reverse
- **LED**: On=forward, Off=reverse
- **Safety**: Motors stop if no signal for 500ms

### Configuration via CLI
```bash
python tools/cli.py /dev/ttyUSB0

>>> config.show()
Paired: True
Train MAC: 12:34:56:78:9A:BC

>>> config.unpair()
Unpaired successfully
```

## Testing

### Unit Tests (Host)
```bash
python -m pytest tests/
```

### Hardware-in-Loop Tests
```bash
# Flash HWIL test to device (Windows example with COM port)
mpremote connect COM3 fs cp hwil/test_button.py :main.py

# Linux/Mac example
mpremote connect /dev/ttyUSB0 fs cp hwil/test_button.py :main.py

# Monitor serial output with mpremote
mpremote connect COM3 repl

# Or use screen on Linux/Mac
screen /dev/ttyUSB0 115200
```

## Safety Features

- 500ms communication timeout stops motors if signal lost
- BMS protection: overcharge, over-discharge, short-circuit
- Paired MAC filtering prevents unauthorized control
- Motor safety stop on receiver boot

## Future Enhancements

- [ ] Battery level monitoring (receiver → controller telemetry)
- [ ] Multiple train support (train selector on controller)
- [ ] Speed limit profiles (parental controls)
- [ ] Additional GPIO features (lights, sound effects)
- [ ] Remote configuration over ESP-NOW
- [ ] Web-based configuration interface

## License

See [LICENSE](LICENSE) file for details.

## References

- Build guide: `docs/lego_pf_controller_build_guide.pdf`
- ESP-NOW documentation: https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/api-reference/network/esp_now.html
- MicroPython ESP32: https://docs.micropython.org/en/latest/esp32/quickref.html
