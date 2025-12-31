"""
Unit tests for LED module

Run with: python -m pytest tests/test_led.py -v
"""

import sys
import time
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


class MockPin:
    """Mock Pin class for testing."""

    def __init__(self, pin_num, mode):
        self.pin_num = pin_num
        self.mode = mode
        self._value = 0

    def value(self, val=None):
        """Get or set pin value."""
        if val is not None:
            self._value = val
        return self._value


class TestLED:
    """Test LED pattern control."""

    def test_initial_state_off(self):
        """Test LED starts in off state."""
        from led import LED

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        assert led.is_on() is False
        assert pin.value() == 0  # Active high, off = 0

    def test_solid_on(self):
        """Test solid on pattern."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.SOLID_ON)
        assert led.is_on() is True
        assert pin.value() == 1

    def test_solid_off(self):
        """Test solid off pattern."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.SOLID_ON)
        led.set_pattern(Pattern.SOLID_OFF)

        assert led.is_on() is False
        assert pin.value() == 0

    def test_active_low(self):
        """Test active low configuration."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=False)

        # Off state - pin should be high for active low
        assert pin.value() == 1

        # On state - pin should be low for active low
        led.set_pattern(Pattern.SOLID_ON)
        assert led.is_on() is True
        assert pin.value() == 0

    def test_blink_slow_timing(self):
        """Test slow blink pattern timing."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.BLINK_SLOW)

        # Should start ON
        assert led.is_on() is True
        assert pin.value() == 1

        # Update before 500ms - should stay ON
        time.sleep(0.4)
        led.update()
        assert led.is_on() is True

        # Update after 500ms - should turn OFF
        time.sleep(0.15)  # Total ~550ms
        led.update()
        assert led.is_on() is False
        assert pin.value() == 0

        # Update after another 500ms - should turn ON
        time.sleep(0.5)
        led.update()
        assert led.is_on() is True
        assert pin.value() == 1

    def test_blink_fast_timing(self):
        """Test fast blink pattern timing."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.BLINK_FAST)

        # Should start ON
        assert led.is_on() is True

        # Update before 100ms - should stay ON
        time.sleep(0.05)
        led.update()
        assert led.is_on() is True

        # Update after 100ms - should turn OFF
        time.sleep(0.06)
        led.update()
        assert led.is_on() is False

        # Update after another 100ms - should turn ON
        time.sleep(0.1)
        led.update()
        assert led.is_on() is True

    def test_blink_very_fast_timing(self):
        """Test very fast blink pattern (pairing mode)."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.BLINK_VERY_FAST)

        # Should start ON
        assert led.is_on() is True

        # Multiple rapid toggles
        for _ in range(5):
            time.sleep(0.06)
            led.update()
            current_state = led.is_on()
            time.sleep(0.06)
            led.update()
            # Should have toggled
            assert led.is_on() != current_state

    def test_pattern_switching(self):
        """Test switching between patterns."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        # Start with slow blink
        led.set_pattern(Pattern.BLINK_SLOW)
        assert led.get_pattern() == Pattern.BLINK_SLOW

        # Switch to solid on
        led.set_pattern(Pattern.SOLID_ON)
        assert led.get_pattern() == Pattern.SOLID_ON
        assert led.is_on() is True

        # Update shouldn't change state (solid pattern)
        led.update()
        assert led.is_on() is True

        # Switch to fast blink
        led.set_pattern(Pattern.BLINK_FAST)
        assert led.get_pattern() == Pattern.BLINK_FAST

    def test_convenience_methods(self):
        """Test turn_on/turn_off convenience methods."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.turn_on()
        assert led.is_on() is True
        assert led.get_pattern() == Pattern.SOLID_ON

        led.turn_off()
        assert led.is_on() is False
        assert led.get_pattern() == Pattern.SOLID_OFF

    def test_get_pattern(self):
        """Test get_pattern method."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        # Default should be off
        assert led.get_pattern() == Pattern.SOLID_OFF

        led.set_pattern(Pattern.BLINK_FAST)
        assert led.get_pattern() == Pattern.BLINK_FAST

    def test_invalid_pattern(self):
        """Test invalid pattern raises error."""
        from led import LED

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        try:
            led.set_pattern(999)  # Invalid pattern
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid pattern" in str(e)

    def test_multiple_blink_cycles(self):
        """Test LED blinks multiple times correctly."""
        from led import LED, Pattern

        pin = MockPin(2, None)
        led = LED(pin, active_high=True)

        led.set_pattern(Pattern.BLINK_FAST)

        # Simulate multiple blink cycles
        toggle_count = 0
        prev_state = led.is_on()

        for _ in range(10):
            time.sleep(0.11)  # Slightly over 100ms
            led.update()
            current_state = led.is_on()

            if current_state != prev_state:
                toggle_count += 1
                prev_state = current_state

        # Should have toggled multiple times (at least 8 out of 10)
        assert toggle_count >= 8


print("LED tests created successfully")
