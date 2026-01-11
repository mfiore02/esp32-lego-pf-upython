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

See [MPREMOTE_GUIDE.md](MPREMOTE_GUIDE.md) for detailed mpremote usage examples and manual deployment instructions.
