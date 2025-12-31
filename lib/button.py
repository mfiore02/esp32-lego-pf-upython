"""
Debounced Button Input Module

Provides reliable button input with debouncing, edge detection, and long press support.
Compatible with MicroPython polling-based event loops.

Example usage:
    from machine import Pin
    from button import Button

    # Create button on GPIO1, active low (pulled high, pressed = low)
    btn = Button(Pin(1, Pin.IN, Pin.PULL_UP), active_low=True)

    # In main loop
    while True:
        btn.update()

        if btn.was_pressed():
            print("Button pressed!")

        if btn.was_released():
            duration = btn.last_press_duration()
            if duration > 1000:
                print("Long press detected:", duration, "ms")

        time.sleep_ms(10)
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


class Button:
    """Debounced button input handler."""

    def __init__(self, pin, active_low=True, debounce_ms=50):
        """
        Initialize button handler.

        Args:
            pin: machine.Pin object configured as input
            active_low: True if button pulls pin low when pressed (default: True)
            debounce_ms: Debounce time in milliseconds (default: 50ms)
        """
        self.pin = pin
        self.active_low = active_low
        self.debounce_ms = debounce_ms

        # State tracking
        self._state = False  # Current debounced state (True = pressed)
        self._raw_state = self._read_raw()  # Last raw pin reading
        self._last_change_time = ticks_ms()  # Time of last state change

        # Edge detection flags
        self._pressed_flag = False  # Set when button is pressed
        self._released_flag = False  # Set when button is released

        # Press timing
        self._press_start_time = 0  # When current press started
        self._last_press_duration = 0  # Duration of last completed press

    def update(self):
        """
        Update button state. Must be called regularly (e.g., in main loop).

        This method reads the pin, applies debouncing, and sets edge detection flags.
        """
        current_time = ticks_ms()
        raw_state = self._read_raw()

        # Check if raw state has changed
        if raw_state != self._raw_state:
            self._raw_state = raw_state
            self._last_change_time = current_time

        # Check if state has been stable long enough to debounce
        time_since_change = ticks_diff(current_time, self._last_change_time)

        if time_since_change >= self.debounce_ms:
            # Raw state is stable, update debounced state
            if raw_state != self._state:
                self._state = raw_state

                # Set edge detection flags
                if self._state:  # Button pressed
                    self._pressed_flag = True
                    self._press_start_time = current_time
                else:  # Button released
                    self._released_flag = True
                    if self._press_start_time > 0:
                        self._last_press_duration = ticks_diff(
                            current_time, self._press_start_time
                        )

    def is_pressed(self):
        """
        Check if button is currently pressed.

        Returns:
            True if button is pressed, False otherwise
        """
        return self._state

    def was_pressed(self):
        """
        Check if button was pressed since last check (edge detection).

        This flag is automatically cleared when read.

        Returns:
            True if button was pressed, False otherwise
        """
        if self._pressed_flag:
            self._pressed_flag = False
            return True
        return False

    def was_released(self):
        """
        Check if button was released since last check (edge detection).

        This flag is automatically cleared when read.

        Returns:
            True if button was released, False otherwise
        """
        if self._released_flag:
            self._released_flag = False
            return True
        return False

    def press_duration(self):
        """
        Get duration of current press in milliseconds.

        Returns:
            Duration in ms if button is currently pressed, 0 otherwise
        """
        if self._state and self._press_start_time > 0:
            return ticks_diff(ticks_ms(), self._press_start_time)
        return 0

    def last_press_duration(self):
        """
        Get duration of last completed press in milliseconds.

        Returns:
            Duration of last press in ms, 0 if no press completed yet
        """
        return self._last_press_duration

    def _read_raw(self):
        """
        Read raw pin state and convert to logical button state.

        Returns:
            True if button is physically pressed, False otherwise
        """
        pin_value = self.pin.value()

        if self.active_low:
            # Pin low (0) means pressed
            return pin_value == 0
        else:
            # Pin high (1) means pressed
            return pin_value == 1
