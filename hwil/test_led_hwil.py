"""
Hardware-in-Loop Test for LED Module

This script tests the LED module on actual ESP32 hardware.

To run:
    1. Flash to device:
       mpremote connect COM3 fs cp hwil/test_led_hwil.py :main.py
       mpremote connect COM3 fs cp lib/led.py :lib/led.py

    2. Monitor output:
       mpremote connect COM3 repl

Expected behavior:
    - LED cycles through different patterns
    - Each pattern runs for 3 seconds
    - Serial output describes current pattern

Hardware setup:
    - Controller: LED on GPIO8 (with 1K resistor to ground)
    - Receiver: LED on GPIO8 (with 1K resistor to ground)
    - Status LED connected to GPIO8 (active high)
"""

import sys
import time
from machine import Pin

# Add lib to path if needed
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from led import LED, Pattern


def test_all_patterns():
    """Test all LED patterns sequentially."""

    print("\n" + "="*50)
    print("LED HWIL Test - Pattern Demo")
    print("="*50)

    # Configure LED pin - GPIO8 for both controller and receiver status LED
    LED_GPIO = 8

    print("Configuring LED on GPIO", LED_GPIO)
    pin = Pin(LED_GPIO, Pin.OUT)
    led = LED(pin, active_high=True)

    print("LED initialized")
    print("\nCycling through patterns...")
    print("Each pattern runs for 3 seconds\n")

    patterns = [
        (Pattern.SOLID_OFF, "SOLID OFF (LED should be off)"),
        (Pattern.SOLID_ON, "SOLID ON (LED should be constantly on)"),
        (Pattern.BLINK_SLOW, "BLINK SLOW (500ms on, 500ms off)"),
        (Pattern.BLINK_FAST, "BLINK FAST (100ms on, 100ms off)"),
        (Pattern.BLINK_VERY_FAST, "BLINK VERY FAST (50ms on, 50ms off - Pairing mode)"),
    ]

    pattern_duration = 3000  # 3 seconds per pattern

    try:
        cycle = 0
        while True:
            cycle += 1
            print("\n--- Cycle {} ---".format(cycle))

            for pattern, description in patterns:
                print("\n[{}] Setting pattern: {}".format(
                    time.ticks_ms(), description
                ))

                led.set_pattern(pattern)
                start_time = time.ticks_ms()

                # Run pattern for specified duration
                while time.ticks_diff(time.ticks_ms(), start_time) < pattern_duration:
                    led.update()
                    time.sleep_ms(10)

            print("\n--- Cycle {} complete ---".format(cycle))
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        led.turn_off()
        print("LED turned off")


def test_interactive():
    """
    Interactive LED test - use REPL to test different patterns.

    This allows manual testing of individual patterns.
    """

    print("\n" + "="*50)
    print("LED Interactive Test")
    print("="*50)

    LED_GPIO = 8  # Controller/Receiver status LED

    print("Configuring LED on GPIO", LED_GPIO)
    pin = Pin(LED_GPIO, Pin.OUT)
    led = LED(pin, active_high=True)

    print("\nLED configured. Use REPL to test patterns:")
    print("  led.turn_on()")
    print("  led.turn_off()")
    print("  led.set_pattern(Pattern.BLINK_FAST)")
    print("\nAvailable patterns:")
    print("  Pattern.SOLID_OFF")
    print("  Pattern.SOLID_ON")
    print("  Pattern.BLINK_SLOW")
    print("  Pattern.BLINK_FAST")
    print("  Pattern.BLINK_VERY_FAST")
    print("\nDon't forget to call led.update() in a loop for blinking patterns!")

    # Make led available in global scope for REPL
    globals()['led'] = led
    globals()['Pattern'] = Pattern

    # Run update loop in background
    print("\nStarting update loop (Ctrl+C to stop)...")
    try:
        while True:
            led.update()
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("\nUpdate loop stopped")
        led.turn_off()


def test_timing_accuracy():
    """
    Test timing accuracy of blink patterns.

    Measures actual toggle times and compares to expected.
    """

    print("\n" + "="*50)
    print("LED Timing Accuracy Test")
    print("="*50)

    LED_GPIO = 8  # Controller/Receiver status LED

    print("Configuring LED on GPIO", LED_GPIO)
    pin = Pin(LED_GPIO, Pin.OUT)
    led = LED(pin, active_high=True)

    # Test fast blink timing (100ms expected)
    print("\nTesting BLINK_FAST pattern (100ms on, 100ms off)")
    led.set_pattern(Pattern.BLINK_FAST)

    toggle_times = []
    prev_state = led.is_on()
    test_duration = 5000  # Test for 5 seconds
    start_time = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        led.update()
        current_state = led.is_on()

        if current_state != prev_state:
            toggle_time = time.ticks_ms()
            toggle_times.append(toggle_time)
            prev_state = current_state

        time.sleep_ms(5)

    # Calculate intervals between toggles
    if len(toggle_times) > 1:
        intervals = []
        for i in range(1, len(toggle_times)):
            interval = time.ticks_diff(toggle_times[i], toggle_times[i-1])
            intervals.append(interval)

        avg_interval = sum(intervals) // len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        print("\nResults:")
        print("  Total toggles:", len(toggle_times))
        print("  Average interval:", avg_interval, "ms (expected: 100ms)")
        print("  Min interval:", min_interval, "ms")
        print("  Max interval:", max_interval, "ms")

        if 95 <= avg_interval <= 105:
            print("  Status: PASS (within 5% tolerance)")
        else:
            print("  Status: FAIL (outside tolerance)")
    else:
        print("Not enough toggles detected")

    led.turn_off()


# Run the pattern demo by default
# Uncomment other tests as needed
if __name__ == "__main__":
    test_all_patterns()
    # test_interactive()
    # test_timing_accuracy()
