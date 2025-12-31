"""
Unit tests for Button module

Run with: python -m pytest tests/test_button.py -v
"""

import sys
import time
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


class MockPin:
    """Mock Pin class for testing."""

    def __init__(self, pin_num, mode, pull=None):
        self.pin_num = pin_num
        self.mode = mode
        self.pull = pull
        self._value = 1  # Default high (unpressed for active_low)

    def value(self):
        """Get pin value."""
        return self._value

    def set_value(self, val):
        """Set pin value for testing."""
        self._value = val


class TestButton:
    """Test button debouncing and edge detection."""

    def test_initial_state_unpressed(self):
        """Test button starts in unpressed state."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # High = unpressed for active_low
        btn = Button(pin, active_low=True)

        assert btn.is_pressed() is False
        assert btn.press_duration() == 0

    def test_initial_state_pressed(self):
        """Test button can start in pressed state."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(0)  # Low = pressed for active_low
        btn = Button(pin, active_low=True)

        # Need to update to read initial state
        btn.update()
        time.sleep(0.06)  # Wait for debounce (50ms default)
        btn.update()

        assert btn.is_pressed() is True

    def test_press_detection(self):
        """Test button press detection."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()
        assert btn.was_pressed() is False

        # Press button
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)  # Wait for debounce
        btn.update()

        assert btn.is_pressed() is True
        assert btn.was_pressed() is True
        assert btn.was_pressed() is False  # Flag cleared after read

    def test_release_detection(self):
        """Test button release detection."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(0)  # Start pressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()
        time.sleep(0.06)
        btn.update()

        assert btn.is_pressed() is True

        # Release button
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()

        assert btn.is_pressed() is False
        assert btn.was_released() is True
        assert btn.was_released() is False  # Flag cleared after read

    def test_debouncing(self):
        """Test that button debounces rapid changes."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()

        # Simulate bouncing - rapid changes
        pin.set_value(0)
        btn.update()
        time.sleep(0.01)  # Only 10ms - not enough to debounce
        pin.set_value(1)
        btn.update()
        time.sleep(0.01)
        pin.set_value(0)
        btn.update()

        # State should not have changed yet
        assert btn.is_pressed() is False

        # Wait for debounce
        time.sleep(0.06)
        btn.update()

        # Now it should register as pressed
        assert btn.is_pressed() is True

    def test_press_duration(self):
        """Test press duration measurement."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()

        # Press button
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)  # Debounce
        btn.update()

        # Wait a bit while pressed
        time.sleep(0.1)
        btn.update()

        # Check duration is roughly correct (allow some tolerance)
        duration = btn.press_duration()
        assert duration >= 90  # At least 90ms (100ms - tolerance)
        assert duration < 200  # But not too long

    def test_last_press_duration(self):
        """Test last press duration is stored."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()

        # Press button
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)
        btn.update()

        # Hold for 100ms
        time.sleep(0.1)
        btn.update()

        # Release
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()

        # Check last press duration
        last_duration = btn.last_press_duration()
        assert last_duration >= 90  # At least 90ms
        assert last_duration < 200

        # Current press duration should be 0
        assert btn.press_duration() == 0

    def test_active_high(self):
        """Test button with active_high configuration."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(0)  # Low = unpressed for active_high
        btn = Button(pin, active_low=False, debounce_ms=50)

        btn.update()
        assert btn.is_pressed() is False

        # Press button (high for active_high)
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()

        assert btn.is_pressed() is True
        assert btn.was_pressed() is True

    def test_multiple_presses(self):
        """Test multiple press/release cycles."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()

        # First press
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)
        btn.update()
        assert btn.was_pressed() is True

        # First release
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()
        assert btn.was_released() is True

        # Second press
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)
        btn.update()
        assert btn.was_pressed() is True

        # Second release
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()
        assert btn.was_released() is True

    def test_long_press_detection(self):
        """Test detecting long press (useful for pairing mode)."""
        from button import Button

        pin = MockPin(1, None, None)
        pin.set_value(1)  # Start unpressed
        btn = Button(pin, active_low=True, debounce_ms=50)

        btn.update()

        # Press and hold
        pin.set_value(0)
        btn.update()
        time.sleep(0.06)  # Debounce
        btn.update()

        # Check short press
        time.sleep(0.1)
        btn.update()
        assert btn.press_duration() >= 90

        # Continue holding for long press
        time.sleep(0.5)  # Total ~600ms
        btn.update()

        # Should detect as long press
        duration = btn.press_duration()
        assert duration >= 550  # At least 550ms

        # Release and check duration was recorded
        pin.set_value(1)
        btn.update()
        time.sleep(0.06)
        btn.update()

        assert btn.last_press_duration() >= 550


print("Button tests created successfully")
