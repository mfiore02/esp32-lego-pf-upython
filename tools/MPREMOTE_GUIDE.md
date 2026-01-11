# mpremote Quick Reference Guide

`mpremote` is the official MicroPython remote control tool for interacting with ESP32 devices.

## Basic Commands

### Connect to Device

**Windows:**
```bash
mpremote connect COM3
```

**Linux/Mac:**
```bash
mpremote connect /dev/ttyUSB0
```

### File Operations

**Copy file to device:**
```bash
# Copy to root
mpremote connect COM3 fs cp local_file.py :remote_file.py

# Copy to /lib directory
mpremote connect COM3 fs cp lib/module.py :/lib/module.py
```

**Copy file from device:**
```bash
mpremote connect COM3 fs cp :remote_file.py local_file.py
```

**List files on device:**
```bash
mpremote connect COM3 fs ls
mpremote connect COM3 fs ls :/lib
```

**Remove file from device:**
```bash
mpremote connect COM3 fs rm :file.py
```

**Create directory:**
```bash
mpremote connect COM3 fs mkdir /lib
```

### Device Control

**Reset device:**
```bash
mpremote connect COM3 reset
```

**Enter REPL (interactive Python):**
```bash
mpremote connect COM3 repl
# Press Ctrl+] to exit REPL
```

**Run a Python command:**
```bash
mpremote connect COM3 exec "print('Hello from ESP32')"
mpremote connect COM3 exec "import machine; print(machine.unique_id())"
```

**Run a local Python script on device:**
```bash
mpremote connect COM3 run script.py
```

### Filesystem Management

**Show disk usage:**
```bash
mpremote connect COM3 fs df
```

**Erase all files (careful!):**
```bash
mpremote connect COM3 fs rmdir :
```

## Deployment Workflow for this Project

### Deploy HWIL Test (Easy Way)

**Windows:**
```bash
.\tools\deploy_hwil_test.bat COM3 test_config_manager
mpremote connect COM3 repl
```

**Linux/Mac:**
```bash
./tools/deploy_hwil_test.sh /dev/ttyUSB0 test_config_manager
mpremote connect /dev/ttyUSB0 repl
```

### Deploy HWIL Test (Manual)

```bash
# 1. Create lib directory
mpremote connect COM3 fs mkdir /lib

# 2. Copy required library
mpremote connect COM3 fs cp lib/config_manager.py :/lib/config_manager.py

# 3. Copy test as main.py
mpremote connect COM3 fs cp hwil/test_config_manager.py :main.py

# 4. Reset and monitor
mpremote connect COM3 reset
mpremote connect COM3 repl
```

### Deploy Application Code

**Controller:**
```bash
# Copy shared libraries
mpremote connect COM3 fs mkdir /lib
mpremote connect COM3 fs cp lib/config_manager.py :/lib/config_manager.py
mpremote connect COM3 fs cp lib/button.py :/lib/button.py
mpremote connect COM3 fs cp lib/led.py :/lib/led.py
mpremote connect COM3 fs cp lib/potentiometer.py :/lib/potentiometer.py
mpremote connect COM3 fs cp lib/espnow_protocol.py :/lib/espnow_protocol.py
mpremote connect COM3 fs cp lib/hardware.py :/lib/hardware.py

# Copy controller app
mpremote connect COM3 fs cp controller/boot.py :boot.py
mpremote connect COM3 fs cp controller/main.py :main.py

# Reset
mpremote connect COM3 reset
```

**Receiver:**
```bash
# Copy shared libraries
mpremote connect COM3 fs mkdir /lib
mpremote connect COM3 fs cp lib/config_manager.py :/lib/config_manager.py
mpremote connect COM3 fs cp lib/button.py :/lib/button.py
mpremote connect COM3 fs cp lib/motor_driver.py :/lib/motor_driver.py
mpremote connect COM3 fs cp lib/espnow_protocol.py :/lib/espnow_protocol.py
mpremote connect COM3 fs cp lib/hardware.py :/lib/hardware.py

# Copy receiver app
mpremote connect COM3 fs cp receiver/boot.py :boot.py
mpremote connect COM3 fs cp receiver/main.py :main.py

# Reset
mpremote connect COM3 reset
```

## Troubleshooting

### Find COM Port (Windows)
Check Device Manager → Ports (COM & LPT) → USB-SERIAL CH340

Or use PowerShell:
```powershell
Get-WmiObject Win32_SerialPort | Select-Object Name,DeviceID
```

### Find Device Port (Linux)
```bash
ls /dev/ttyUSB*
# or
ls /dev/ttyACM*
```

### Find Device Port (Mac)
```bash
ls /dev/cu.usbserial-*
# or
ls /dev/cu.wchusbserial*
```

### Permission Denied (Linux)
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in

# Or use sudo
sudo mpremote connect /dev/ttyUSB0 repl
```

### Device Not Responding
1. Check USB cable (must be data cable, not charge-only)
2. Press RESET button on ESP32
3. Try different USB port
4. Unplug and replug device

### REPL Not Responding
Press Ctrl+C to interrupt running program, then Ctrl+D for soft reset

## Useful mpremote Tips

**Chain commands:**
```bash
mpremote connect COM3 fs cp test.py :main.py + reset + repl
```

**Use shortcuts:**
```bash
# Auto-detect port (if only one device connected)
mpremote fs ls

# Set default connection
export MPREMOTE_DEVICE=/dev/ttyUSB0
mpremote fs ls
```

**Mount local filesystem (advanced):**
```bash
mpremote connect COM3 mount .
# Device can now import modules from current directory
```

## References

- Official mpremote docs: https://docs.micropython.org/en/latest/reference/mpremote.html
- MicroPython ESP32 guide: https://docs.micropython.org/en/latest/esp32/quickref.html
