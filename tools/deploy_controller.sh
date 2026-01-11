#!/bin/bash
# Deploy Controller Application to ESP32
# Usage: ./deploy_controller.sh PORT
# Example: ./deploy_controller.sh COM3
# Example (Linux/Mac): ./deploy_controller.sh /dev/ttyUSB0

if [ -z "$1" ]; then
    echo "Usage: deploy_controller.sh PORT"
    echo "Example (Windows): ./deploy_controller.sh COM3"
    echo "Example (Linux/Mac): ./deploy_controller.sh /dev/ttyUSB0"
    exit 1
fi

PORT=$1

echo "=========================================="
echo "Deploying Controller to $PORT"
echo "=========================================="

# Create lib directory
echo "Creating /lib directory..."
mpremote connect $PORT fs mkdir /lib 2>/dev/null || true

# Copy all library modules
echo "Copying library modules..."
mpremote connect $PORT fs cp lib/config_manager.py :/lib/config_manager.py
mpremote connect $PORT fs cp lib/button.py :/lib/button.py
mpremote connect $PORT fs cp lib/led.py :/lib/led.py
mpremote connect $PORT fs cp lib/potentiometer.py :/lib/potentiometer.py
mpremote connect $PORT fs cp lib/motor_driver.py :/lib/motor_driver.py
mpremote connect $PORT fs cp lib/espnow_protocol.py :/lib/espnow_protocol.py
mpremote connect $PORT fs cp lib/hardware.py :/lib/hardware.py

# Copy controller main application
echo "Copying controller application..."
mpremote connect $PORT fs cp controller/main.py :main.py

# Reset device to start application
echo "Resetting device..."
mpremote connect $PORT reset

echo ""
echo "=========================================="
echo "Controller deployed successfully!"
echo "=========================================="
echo ""
echo "The controller will start automatically."
echo "To monitor output, connect to REPL:"
echo "  mpremote connect $PORT repl"
echo ""
echo "To enter pairing mode:"
echo "  Hold the button during power-up"
echo ""
