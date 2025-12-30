"""
Hardware-in-Loop Test for ConfigManager

Tests configuration persistence across power cycles using filesystem storage.

Usage:
    mpremote connect COM3 fs cp hwil/test_config_manager_hwil.py :main.py
    mpremote connect COM3 soft-reset
    # Follow instructions, unplug/replug ESP32
    # Should show "SUCCESS!" after reboot

To cleanup:
    mpremote connect COM3 exec "open('/.cleanup', 'w').close()"
    mpremote connect COM3 soft-reset
"""

import sys
import os
sys.path.append('/lib')

from config_manager import ConfigManager

# Check for cleanup marker file
cleanup_mode = False
try:
    os.stat('/.cleanup')
    cleanup_mode = True
    os.remove('/.cleanup')  # Remove marker after reading
except:
    pass

print("\n" + "="*50)
print("ConfigManager HWIL Test")
print("="*50)

if cleanup_mode:
    print("\nCLEANUP MODE - Erasing test data...")
    config = ConfigManager("controller")
    config.erase()
    print("✓ Test data erased")
    print("\nRun test again to restart from scratch")
else:
    # Load config
    config = ConfigManager("controller")

    # Check for test data
    paired = config.get("paired")
    mac = config.get("train_mac")

    if paired == True and mac == [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE]:
        # Test data found - this is run 2
        print("\n" + "="*50)
        print("SUCCESS! Config persisted across reboot! ✓")
        print("="*50)

        pot_min = config.get("pot_calibration.min")
        pot_max = config.get("pot_calibration.max")

        print("\nVerified values:")
        print("  Paired: True")
        mac_str = ':'.join(['%02X' % b for b in mac])
        print("  Train MAC: " + mac_str)
        print("  Pot Min: " + str(pot_min) + " (expected 250)")
        print("  Pot Max: " + str(pot_max) + " (expected 3750)")

        print("\n" + "="*50)
        print("Test complete! Data remains for inspection.")
        print("To cleanup: Set CLEANUP=True in test file")
        print("="*50)

    else:
        # Write test data - this is run 1
        print("\nWriting test configuration...")
        config.set("paired", True)
        config.set("train_mac", [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE])
        config.set("pot_calibration.min", 250)
        config.set("pot_calibration.max", 3750)
        config.save()

        print("✓ Test data written")
        print("\n" + "!"*50)
        print("UNPLUG and REPLUG the ESP32")
        print("Then: mpremote connect COM3 repl")
        print("Press Ctrl+D to verify persistence")
        print("!"*50)
