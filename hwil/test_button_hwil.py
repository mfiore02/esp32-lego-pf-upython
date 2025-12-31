"""
Hardware-in-Loop Test for Button Module

This script tests the button module on actual ESP32 hardware.

To run:
    1. Flash to device:
       mpremote connect COM3 fs cp hwil/test_button.py :main.py
       mpremote connect COM3 fs cp lib/button.py :lib/button.py

    2. Monitor output:
       mpremote connect COM3 repl

Expected behavior:
    - Press button briefly: Reports "Short press" with duration
    - Hold button for >1 second: Reports "Long press" with duration
    - Multiple presses: Each detected separately

Hardware setup:
    - Controller: Button on GPIO1 (with pull-up, active low)
    - Receiver: Button on GPIO9/BOOT (with pull-up, active low)
    - Or any GPIO with a button connected (active low with pull-up)
"""

import sys
import time
from machine import Pin

# Add lib to path if needed
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from button import Button


def test_button():
    """Test button functionality on hardware."""

    print("\n" + "="*50)
    print("Button HWIL Test")
    print("="*50)

    # Configure button pin - change GPIO number as needed
    # GPIO1 for controller, GPIO9 for receiver (BOOT button)
    BUTTON_GPIO = 1  # Change to 1 for controller testing

    print("Configuring button on GPIO", BUTTON_GPIO)
    pin = Pin(BUTTON_GPIO, Pin.IN, Pin.PULL_UP)
    btn = Button(pin, active_low=True, debounce_ms=50)

    print("Button initialized")
    print("Press the button to test...")
    print("Hold for >1 second to test long press detection")
    print("Press Ctrl+C to exit\n")

    press_count = 0
    last_report_time = time.ticks_ms()

    try:
        while True:
            # Update button state
            btn.update()

            # Check for press event
            if btn.was_pressed():
                press_count += 1
                print("[{}] Button PRESSED (count: {})".format(
                    time.ticks_ms(), press_count
                ))

            # Check for release event
            if btn.was_released():
                duration = btn.last_press_duration()
                if duration > 1000:
                    print("[{}] Button RELEASED - LONG PRESS ({} ms)".format(
                        time.ticks_ms(), duration
                    ))
                else:
                    print("[{}] Button RELEASED - Short press ({} ms)".format(
                        time.ticks_ms(), duration
                    ))

            # Show current state every 5 seconds
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_report_time) > 5000:
                if btn.is_pressed():
                    current_duration = btn.press_duration()
                    print("\n[Status] Button is HELD for {} ms".format(current_duration))
                else:
                    print("\n[Status] Waiting for button press... (total presses: {})".format(
                        press_count
                    ))
                last_report_time = current_time

            # Small delay to prevent tight loop
            time.sleep_ms(10)

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        print("Total button presses detected:", press_count)


def test_debouncing():
    """
    Test debouncing by monitoring raw state changes vs debounced state.

    This is more advanced testing to verify debouncing is working.
    """

    print("\n" + "="*50)
    print("Debouncing Test")
    print("="*50)

    BUTTON_GPIO = 9  # Change as needed

    print("Configuring button on GPIO", BUTTON_GPIO)
    pin = Pin(BUTTON_GPIO, Pin.IN, Pin.PULL_UP)
    btn = Button(pin, active_low=True, debounce_ms=50)

    print("This test monitors debouncing behavior")
    print("Press button quickly and observe output")
    print("Press Ctrl+C to exit\n")

    last_raw_state = pin.value()
    last_debounced_state = False
    raw_change_count = 0
    debounced_change_count = 0

    try:
        while True:
            btn.update()

            # Check raw pin state changes
            current_raw_state = pin.value()
            if current_raw_state != last_raw_state:
                raw_change_count += 1
                print("[RAW] Pin changed to", current_raw_state, "(change #{})".format(
                    raw_change_count
                ))
                last_raw_state = current_raw_state

            # Check debounced state changes
            current_debounced_state = btn.is_pressed()
            if current_debounced_state != last_debounced_state:
                debounced_change_count += 1
                print("  [DEBOUNCED] Button state:", current_debounced_state, "(change #{})".format(
                    debounced_change_count
                ))
                last_debounced_state = current_debounced_state

            time.sleep_ms(1)  # Very fast polling to catch bounces

    except KeyboardInterrupt:
        print("\n\nDebouncing Test Results:")
        print("Raw state changes:", raw_change_count)
        print("Debounced state changes:", debounced_change_count)
        print("Bounces filtered:", raw_change_count - debounced_change_count)


# Run the basic test by default
# Uncomment the line below to run debouncing test instead
if __name__ == "__main__":
    test_button()
    # test_debouncing()  # Uncomment to run debouncing test
