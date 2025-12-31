"""
LED Pattern Control Module

Provides pattern-based LED control for status indication.
Compatible with MicroPython polling-based event loops.

Example usage:
    from machine import Pin
    from led import LED, Pattern

    # Create LED on GPIO2
    led = LED(Pin(2, Pin.OUT))

    # Set to solid on (forward mode)
    led.set_pattern(Pattern.SOLID_ON)

    # In main loop
    while True:
        led.update()
        time.sleep_ms(10)

    # Pairing mode - rapid blink
    led.set_pattern(Pattern.BLINK_FAST)
"""

import time

# MicroPython compatibility shim for running tests on host
try:
    # Try to use MicroPython's ticks functions
    time.ticks_ms()
    ticks_ms = time.ticks_ms
    ticks_diff = time.ticks_diff
except (AttributeError, TypeError):
    # Fallback to standard Python time functions (for unit tests)
    def ticks_ms():
        return int(time.time() * 1000)

    def ticks_diff(end, start):
        return end - start


class Pattern:
    """LED pattern definitions."""

    SOLID_OFF = 0
    SOLID_ON = 1
    BLINK_SLOW = 2  # 500ms on, 500ms off
    BLINK_FAST = 3  # 100ms on, 100ms off
    BLINK_VERY_FAST = 4  # 50ms on, 50ms off (pairing mode)


class LED:
    """Pattern-based LED controller."""

    # Pattern timing configurations (on_ms, off_ms)
    _PATTERN_TIMING = {
        Pattern.SOLID_OFF: (0, 0),
        Pattern.SOLID_ON: (0, 0),
        Pattern.BLINK_SLOW: (500, 500),
        Pattern.BLINK_FAST: (100, 100),
        Pattern.BLINK_VERY_FAST: (50, 50),
    }

    def __init__(self, pin, active_high=True):
        """
        Initialize LED controller.

        Args:
            pin: machine.Pin object configured as output
            active_high: True if LED turns on when pin is high (default: True)
        """
        self.pin = pin
        self.active_high = active_high

        # State tracking
        self._pattern = Pattern.SOLID_OFF
        self._led_state = False  # Current LED state (True = on)
        self._last_toggle_time = ticks_ms()

        # Initialize pin to off
        self._update_pin()

    def set_pattern(self, pattern):
        """
        Set LED pattern.

        Args:
            pattern: Pattern constant (e.g., Pattern.SOLID_ON)
        """
        if pattern not in self._PATTERN_TIMING:
            raise ValueError("Invalid pattern: " + str(pattern))

        self._pattern = pattern
        self._last_toggle_time = ticks_ms()

        # For solid patterns, set state immediately
        if pattern == Pattern.SOLID_ON:
            self._led_state = True
            self._update_pin()
        elif pattern == Pattern.SOLID_OFF:
            self._led_state = False
            self._update_pin()
        else:
            # For blinking patterns, start with LED on
            self._led_state = True
            self._update_pin()

    def update(self):
        """
        Update LED state based on current pattern.

        Must be called regularly (e.g., in main loop).
        """
        # Solid patterns don't need updates
        if self._pattern == Pattern.SOLID_ON or self._pattern == Pattern.SOLID_OFF:
            return

        # Get timing for current pattern
        on_ms, off_ms = self._PATTERN_TIMING[self._pattern]

        # Calculate time since last toggle
        current_time = ticks_ms()
        elapsed = ticks_diff(current_time, self._last_toggle_time)

        # Determine if it's time to toggle
        should_toggle = False
        if self._led_state and elapsed >= on_ms:
            # LED is on, check if it's time to turn off
            should_toggle = True
        elif not self._led_state and elapsed >= off_ms:
            # LED is off, check if it's time to turn on
            should_toggle = True

        if should_toggle:
            self._led_state = not self._led_state
            self._last_toggle_time = current_time
            self._update_pin()

    def get_pattern(self):
        """
        Get current pattern.

        Returns:
            Current pattern constant
        """
        return self._pattern

    def is_on(self):
        """
        Check if LED is currently on.

        Returns:
            True if LED is on, False otherwise
        """
        return self._led_state

    def turn_on(self):
        """Convenience method to turn LED on (sets SOLID_ON pattern)."""
        self.set_pattern(Pattern.SOLID_ON)

    def turn_off(self):
        """Convenience method to turn LED off (sets SOLID_OFF pattern)."""
        self.set_pattern(Pattern.SOLID_OFF)

    def _update_pin(self):
        """Update physical pin state based on LED state and active level."""
        if self.active_high:
            # Active high: LED on = pin high
            self.pin.value(1 if self._led_state else 0)
        else:
            # Active low: LED on = pin low
            self.pin.value(0 if self._led_state else 1)
