# Development Tools

Deployment and configuration utilities.

## Scripts

### flash_controller.sh
Deploys controller firmware to ESP32-C3.

```bash
./tools/flash_controller.sh /dev/ttyUSB0
```

### flash_receiver.sh
Deploys receiver firmware to ESP32-C3.

```bash
./tools/flash_receiver.sh /dev/ttyUSB0
```

### cli.py
Serial-based configuration tool for devices.

```bash
python tools/cli.py /dev/ttyUSB0

>>> config.show()
>>> config.unpair()
>>> config.set('pot_calibration.min', 150)
```

## Requirements

```bash
pip install esptool adafruit-ampy pyserial
```
