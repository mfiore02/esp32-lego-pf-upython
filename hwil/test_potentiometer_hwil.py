"""
Hardware-in-Loop Test for Potentiometer Module

This script tests the potentiometer module on actual ESP32 hardware.

To run:
    1. Flash to device:
       mpremote connect COM3 fs cp hwil/test_potentiometer_hwil.py :main.py
       mpremote connect COM3 fs cp lib/potentiometer.py :lib/potentiometer.py

    2. Monitor output:
       mpremote connect COM3 repl

Expected behavior:
    - Displays real-time potentiometer readings
    - Shows raw ADC value, calibrated speed (0-100), and visual bar
    - Updates as you turn the potentiometer

Hardware setup:
    - Controller: Potentiometer on GPIO0 (ADC1_CH0)
    - Connect potentiometer: one end to 3.3V, other to GND, wiper to GPIO0
    - 10K linear potentiometer recommended
"""

import sys
import time
from machine import Pin, ADC

# Add lib to path if needed
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from potentiometer import Potentiometer


def test_continuous_read():
    """Continuously read and display potentiometer values."""

    print("\n" + "="*50)
    print("Potentiometer Continuous Read Test")
    print("="*50)

    # Configure ADC - GPIO0 for controller
    POT_GPIO = 0

    print("Configuring potentiometer on GPIO", POT_GPIO)
    adc = ADC(Pin(POT_GPIO))
    adc.atten(ADC.ATTN_11DB)  # Full 0-3.3V range
    adc.width(ADC.WIDTH_12BIT)  # 12-bit resolution (0-4095)

    # Create potentiometer with default calibration
    pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

    print("Potentiometer initialized")
    print("Calibration: min=100, max=3995, zero_band=50")
    print("\nTurn potentiometer to see readings")
    print("Press Ctrl+C to exit\n")

    try:
        while True:
            raw = pot.read_raw()
            speed = pot.read()

            # Create visual bar graph
            bar_length = speed // 2  # Scale to 50 chars max
            bar = '#' * bar_length + '-' * (50 - bar_length)

            print("\rRaw: {:4d}  Speed: {:3d}%  [{}]".format(
                raw, speed, bar
            ), end='')

            time.sleep_ms(50)

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")


def test_calibration_helper():
    """
    Help calibrate potentiometer by tracking min/max values.

    Turn potentiometer to full range and this will report the
    actual min/max ADC values seen.
    """

    print("\n" + "="*50)
    print("Potentiometer Calibration Helper")
    print("="*50)

    POT_GPIO = 0

    print("Configuring ADC on GPIO", POT_GPIO)
    adc = ADC(Pin(POT_GPIO))
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)

    print("\nCalibration procedure:")
    print("1. Turn potentiometer to minimum (fully CCW)")
    print("2. Turn potentiometer to maximum (fully CW)")
    print("3. Repeat several times")
    print("4. Press Ctrl+C when done")
    print("\nStarting in 3 seconds...\n")
    time.sleep(3)

    min_seen = 4095
    max_seen = 0
    sample_count = 0

    try:
        while True:
            raw = adc.read()
            sample_count += 1

            if raw < min_seen:
                min_seen = raw
                print("New minimum detected:", min_seen)

            if raw > max_seen:
                max_seen = raw
                print("New maximum detected:", max_seen)

            # Show current value
            print("\rCurrent: {:4d}  Min: {:4d}  Max: {:4d}  Samples: {}".format(
                raw, min_seen, max_seen, sample_count
            ), end='')

            time.sleep_ms(50)

    except KeyboardInterrupt:
        print("\n\nCalibration complete!")
        print("=" * 50)
        print("Recommended calibration values:")
        print("  min_val:", min_seen)
        print("  max_val:", max_seen)
        print("  zero_band: 50  (or adjust as needed)")
        print("\nUpdate these in your config or code:")
        print("  pot = Potentiometer(adc, min_val={}, max_val={}, zero_band=50)".format(
            min_seen, max_seen
        ))


def test_zero_band():
    """Test zero band behavior."""

    print("\n" + "="*50)
    print("Potentiometer Zero Band Test")
    print("="*50)

    POT_GPIO = 0

    print("Configuring potentiometer on GPIO", POT_GPIO)
    adc = ADC(Pin(POT_GPIO))
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)

    pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

    print("Zero band configured: 50 ADC units")
    print("\nSlowly turn potentiometer from minimum")
    print("Watch when speed changes from 0 to >0")
    print("This should happen when raw > min + zero_band")
    print("Press Ctrl+C to exit\n")

    prev_speed = -1

    try:
        while True:
            raw = pot.read_raw()
            speed = pot.read()

            # Highlight when speed changes from 0
            if speed != prev_speed:
                if prev_speed == 0 and speed > 0:
                    print("\n>>> ZERO BAND EXIT: Raw={}, Speed={}".format(raw, speed))
                elif prev_speed > 0 and speed == 0:
                    print("\n>>> ZERO BAND ENTER: Raw={}, Speed={}".format(raw, speed))

                prev_speed = speed

            in_zero_band = (raw < 100 + 50) if raw >= 100 else True

            print("\rRaw: {:4d}  Speed: {:3d}%  Zero band: {}  ".format(
                raw, speed, "YES" if in_zero_band else "NO "
            ), end='')

            time.sleep_ms(50)

    except KeyboardInterrupt:
        print("\n\nTest stopped")


def test_with_custom_calibration():
    """
    Test with custom calibration values.

    If you've already run calibration helper, enter your values here.
    """

    print("\n" + "="*50)
    print("Potentiometer Test with Custom Calibration")
    print("="*50)

    POT_GPIO = 0

    # EDIT THESE VALUES after running calibration helper
    CUSTOM_MIN = 100
    CUSTOM_MAX = 3995
    CUSTOM_ZERO_BAND = 50

    print("Configuring potentiometer on GPIO", POT_GPIO)
    adc = ADC(Pin(POT_GPIO))
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)

    pot = Potentiometer(adc,
                        min_val=CUSTOM_MIN,
                        max_val=CUSTOM_MAX,
                        zero_band=CUSTOM_ZERO_BAND)

    print("Custom calibration:")
    print("  min_val:", CUSTOM_MIN)
    print("  max_val:", CUSTOM_MAX)
    print("  zero_band:", CUSTOM_ZERO_BAND)
    print("\nTurn potentiometer through full range")
    print("Verify:")
    print("  - At minimum: speed = 0")
    print("  - At maximum: speed = 100")
    print("Press Ctrl+C to exit\n")

    try:
        while True:
            raw = pot.read_raw()
            speed = pot.read()

            # Highlight edges
            status = ""
            if raw <= CUSTOM_MIN:
                status = "(AT MIN)"
            elif raw >= CUSTOM_MAX:
                status = "(AT MAX)"
            elif raw < CUSTOM_MIN + CUSTOM_ZERO_BAND:
                status = "(IN ZERO BAND)"

            bar_length = speed // 2
            bar = '#' * bar_length + '-' * (50 - bar_length)

            print("\rRaw: {:4d}  Speed: {:3d}%  [{}] {}  ".format(
                raw, speed, bar, status
            ), end='')

            time.sleep_ms(50)

    except KeyboardInterrupt:
        print("\n\nTest complete")


# Run continuous read by default
# Uncomment others as needed
if __name__ == "__main__":
    test_continuous_read()
    # test_calibration_helper()
    # test_zero_band()
    # test_with_custom_calibration()
