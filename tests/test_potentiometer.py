"""
Unit tests for Potentiometer module

Run with: python -m pytest tests/test_potentiometer.py -v
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


class MockADC:
    """Mock ADC class for testing."""

    def __init__(self):
        self._value = 0

    def read(self):
        """Return mock ADC value."""
        return self._value

    def set_value(self, val):
        """Set mock ADC value for testing."""
        self._value = val


class TestPotentiometer:
    """Test potentiometer ADC reading and calibration."""

    def test_initialization(self):
        """Test potentiometer initializes with default calibration."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc)

        min_val, max_val, zero_band = pot.get_calibration()
        assert min_val == 100
        assert max_val == 3995
        assert zero_band == 50

    def test_custom_calibration(self):
        """Test potentiometer with custom calibration."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=200, max_val=4000, zero_band=100)

        min_val, max_val, zero_band = pot.get_calibration()
        assert min_val == 200
        assert max_val == 4000
        assert zero_band == 100

    def test_zero_band_at_minimum(self):
        """Test that values within zero band return 0."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # At minimum
        adc.set_value(100)
        assert pot.read() == 0

        # Within zero band
        adc.set_value(120)
        assert pot.read() == 0

        # Just at edge of zero band
        adc.set_value(149)
        assert pot.read() == 0

    def test_just_above_zero_band(self):
        """Test that values just above zero band map correctly."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # Just above zero band
        adc.set_value(150)  # min(100) + zero_band(50)
        speed = pot.read()
        assert speed == 0  # Should be at the start of active range

        # Slightly higher
        adc.set_value(200)
        speed = pot.read()
        assert speed > 0  # Should be slightly above 0

    def test_maximum_value(self):
        """Test that maximum value returns 100."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # At maximum
        adc.set_value(3995)
        assert pot.read() == 100

        # Above maximum (should clamp)
        adc.set_value(4095)
        assert pot.read() == 100

    def test_mid_range_value(self):
        """Test mid-range value maps to approximately 50."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # Calculate mid-point (accounting for zero band)
        # Active range: 150 to 3995
        # Mid-point: 150 + (3995-150)/2 = 150 + 1922.5 = 2072.5
        adc.set_value(2072)
        speed = pot.read()
        assert 48 <= speed <= 52  # Allow small tolerance due to integer division

    def test_below_minimum(self):
        """Test that values below minimum clamp to 0."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # Below minimum
        adc.set_value(50)
        assert pot.read() == 0

        # At zero
        adc.set_value(0)
        assert pot.read() == 0

    def test_read_raw(self):
        """Test read_raw returns unprocessed ADC value."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc)

        adc.set_value(2000)
        assert pot.read_raw() == 2000

        adc.set_value(4095)
        assert pot.read_raw() == 4095

    def test_set_calibration(self):
        """Test updating calibration parameters."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # Update calibration
        pot.set_calibration(min_val=200, max_val=4000, zero_band=100)

        min_val, max_val, zero_band = pot.get_calibration()
        assert min_val == 200
        assert max_val == 4000
        assert zero_band == 100

        # Verify new calibration affects readings
        adc.set_value(200)
        assert pot.read() == 0  # Within new zero band

    def test_invalid_calibration_min_max(self):
        """Test that invalid min/max raises error."""
        from potentiometer import Potentiometer

        adc = MockADC()

        # min >= max should fail
        try:
            pot = Potentiometer(adc, min_val=3000, max_val=2000)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "min_val must be less than max_val" in str(e)

        # Equal values should also fail
        try:
            pot = Potentiometer(adc, min_val=2000, max_val=2000)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "min_val must be less than max_val" in str(e)

    def test_invalid_zero_band(self):
        """Test that negative zero band raises error."""
        from potentiometer import Potentiometer

        adc = MockADC()

        try:
            pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=-10)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "zero_band must be non-negative" in str(e)

    def test_zero_zero_band(self):
        """Test that zero_band=0 works correctly."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=0)

        # At minimum with no zero band
        adc.set_value(100)
        assert pot.read() == 0

        # Significantly above minimum (1 unit is too small to register in large range)
        adc.set_value(150)
        speed = pot.read()
        assert speed > 0  # Should be above 0 now

    def test_large_zero_band(self):
        """Test with large zero band."""
        from potentiometer import Potentiometer

        adc = MockADC()
        # Zero band covers significant portion of range
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=500)

        # Within large zero band
        adc.set_value(500)
        assert pot.read() == 0

        # Just at edge
        adc.set_value(599)
        assert pot.read() == 0

        # Just above
        adc.set_value(600)
        assert pot.read() == 0  # At start of active range

    def test_mapping_linearity(self):
        """Test that mapping is reasonably linear."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        # Test several points across range
        test_points = [
            (150, 0),    # Start of active range
            (2072, 50),  # Mid-point (approximately)
            (3995, 100), # Maximum
        ]

        for raw_val, expected_speed in test_points:
            adc.set_value(raw_val)
            speed = pot.read()
            # Allow tolerance of ±2 for integer math rounding
            assert abs(speed - expected_speed) <= 2, \
                f"At raw={raw_val}, expected ~{expected_speed}, got {speed}"

    def test_full_range_sweep(self):
        """Test sweeping through full range produces monotonic output."""
        from potentiometer import Potentiometer

        adc = MockADC()
        pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

        prev_speed = -1
        for raw_val in range(100, 4000, 100):
            adc.set_value(raw_val)
            speed = pot.read()

            # Speed should never decrease as raw value increases
            assert speed >= prev_speed, \
                f"Non-monotonic at raw={raw_val}: {speed} < {prev_speed}"

            prev_speed = speed


print("Potentiometer tests created successfully")
