#!/bin/bash
# Deploy HWIL test to ESP32 (Linux/Mac)
# Usage: ./deploy_hwil_test.sh /dev/ttyUSB0 test_config_manager_hwil

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: deploy_hwil_test.sh PORT TEST_NAME"
    echo "Example: ./deploy_hwil_test.sh /dev/ttyUSB0 test_config_manager_hwil"
    exit 1
fi

PORT=$1
TEST=$2

echo "Deploying $TEST to $PORT..."

# Create lib directory
mpremote connect $PORT fs mkdir /lib 2>/dev/null || true

# Copy config_manager library
echo "Copying lib/config_manager.py..."
mpremote connect $PORT fs cp lib/config_manager.py :/lib/config_manager.py

# Copy HWIL test as main.py
echo "Copying hwil/${TEST}.py to main.py..."
mpremote connect $PORT fs cp hwil/${TEST}.py :main.py

# Reset device
echo "Resetting device..."
mpremote connect $PORT reset

echo ""
echo "Test deployed! Connect to REPL with:"
echo "  mpremote connect $PORT repl"
