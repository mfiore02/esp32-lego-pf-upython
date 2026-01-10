#!/bin/bash
# Deploy ALL HWIL Tests to ESP32
# Usage: ./deploy_hwil.sh PORT
# Example: ./deploy_hwil.sh COM3
# Example (Linux/Mac): ./deploy_hwil.sh /dev/ttyUSB0

if [ -z "$1" ]; then
    echo "Usage: deploy_hwil.sh PORT"
    echo "Example (Windows): ./deploy_hwil.sh COM3"
    echo "Example (Linux/Mac): ./deploy_hwil.sh /dev/ttyUSB0"
    exit 1
fi

PORT=$1

echo "=========================================="
echo "Deploying HWIL Tests to $PORT"
echo "=========================================="

# Create directories
echo "Creating directories..."
mpremote connect $PORT fs mkdir /lib 2>/dev/null || true
mpremote connect $PORT fs mkdir /hwil 2>/dev/null || true

# Remove main.py if it exists (from previous controller/receiver deployment)
echo "Removing main.py (if exists)..."
mpremote connect $PORT fs rm :main.py 2>/dev/null || true

# Copy all library modules
echo "Copying library modules..."
mpremote connect $PORT fs cp lib/config_manager.py :/lib/config_manager.py
mpremote connect $PORT fs cp lib/button.py :/lib/button.py
mpremote connect $PORT fs cp lib/led.py :/lib/led.py
mpremote connect $PORT fs cp lib/potentiometer.py :/lib/potentiometer.py
mpremote connect $PORT fs cp lib/motor_driver.py :/lib/motor_driver.py
mpremote connect $PORT fs cp lib/espnow_protocol.py :/lib/espnow_protocol.py

# Copy all HWIL test files
echo "Copying HWIL test files..."
mpremote connect $PORT fs cp hwil/test_config_manager_hwil.py :/hwil/test_config_manager_hwil.py
mpremote connect $PORT fs cp hwil/reboot_test_helper.py :/hwil/reboot_test_helper.py
mpremote connect $PORT fs cp hwil/test_button_hwil.py :/hwil/test_button_hwil.py
mpremote connect $PORT fs cp hwil/test_led_hwil.py :/hwil/test_led_hwil.py
mpremote connect $PORT fs cp hwil/test_potentiometer_hwil.py :/hwil/test_potentiometer_hwil.py
mpremote connect $PORT fs cp hwil/test_espnow_protocol_hwil.py :/hwil/test_espnow_protocol_hwil.py
mpremote connect $PORT fs cp hwil/test_motor_driver_hwil.py :/hwil/test_motor_driver_hwil.py

echo ""
echo "=========================================="
echo "HWIL Tests deployed successfully!"
echo "=========================================="
echo ""
echo "Available tests in /hwil/:"
echo "  - test_config_manager_hwil.py"
echo "  - test_button_hwil.py"
echo "  - test_led_hwil.py"
echo "  - test_potentiometer_hwil.py"
echo "  - test_motor_driver_hwil.py"
echo "  - test_espnow_protocol_hwil.py"
echo ""
echo "To run a test, connect to REPL and import it:"
echo "  mpremote connect $PORT repl"
echo ""
echo "Then in the REPL:"
echo "  >>> import hwil.test_button_hwil"
echo "  >>> # Follow on-screen instructions"
echo ""
echo "For ESP-NOW tests with two devices:"
echo "  Device 1: >>> from hwil.test_espnow_protocol_hwil import test_receiver"
echo "            >>> test_receiver()"
echo "  Device 2: >>> from hwil.test_espnow_protocol_hwil import test_sender"
echo "            >>> test_sender()"
echo ""
