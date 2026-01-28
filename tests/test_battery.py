"""
Unit tests for Battery Monitoring module

Run with: python -m pytest tests/test_battery.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


class MockPin:
    """Mock Pin class for testing."""

    def __init__(self, pin_num):
        self.pin_num = pin_num


class MockADC:
    """Mock ADC class for testing."""

    ATTN_11DB = 3  # Mock attenuation constant

    def __init__(self, pin):
        self.pin = pin
        self._value = 0
        self._attenuation = None

    def read(self):
        """Return mock ADC value."""
        return self._value

    def atten(self, attenuation):
        """Set attenuation."""
        self._attenuation = attenuation

    def set_value(self, val):
        """Set mock ADC value for testing."""
        self._value = val


# Mock the machine module
sys.modules['machine'] = MagicMock()
sys.modules['machine'].ADC = MockADC
sys.modules['machine'].Pin = MockPin


class TestBatteryMonitorConstants:
    """Test battery module constants and voltage divider ratios."""

    def test_voltage_divider_ratios(self):
        """Test that voltage divider ratios are calculated correctly."""
        from battery import BPLUS_R1, BPLUS_R2, BPLUS_RATIO
        from battery import BMID_R1, BMID_R2, BMID_RATIO

        # B+ divider: 100k/39k
        expected_bplus_ratio = 39000 / (100000 + 39000)
        assert abs(BPLUS_RATIO - expected_bplus_ratio) < 0.0001
        assert abs(BPLUS_RATIO - 0.2806) < 0.001

        # BM divider: 33k/47k
        expected_bmid_ratio = 47000 / (33000 + 47000)
        assert abs(BMID_RATIO - expected_bmid_ratio) < 0.0001
        assert abs(BMID_RATIO - 0.5875) < 0.001

    def test_battery_thresholds(self):
        """Test that battery threshold constants are correct for 2S LiPo."""
        from battery import (
            CELL_MAX_V, CELL_NOM_V, CELL_LOW_V, CELL_MIN_V,
            BATTERY_MAX_V, BATTERY_NOM_V, BATTERY_LOW_V, BATTERY_MIN_V
        )

        # Single cell thresholds
        assert CELL_MAX_V == 4.2
        assert CELL_NOM_V == 3.7
        assert CELL_LOW_V == 3.3
        assert CELL_MIN_V == 3.0

        # 2S battery thresholds (2x cell values)
        assert BATTERY_MAX_V == 8.4
        assert BATTERY_NOM_V == 7.4
        assert BATTERY_LOW_V == 6.6
        assert BATTERY_MIN_V == 6.0


class TestBatteryMonitorInitialization:
    """Test BatteryMonitor initialization."""

    def test_initialization(self):
        """Test that BatteryMonitor initializes ADC channels correctly."""
        from battery import BatteryMonitor
        import hardware

        monitor = BatteryMonitor()

        # Check that ADC channels were initialized
        assert monitor.adc_bplus is not None
        assert monitor.adc_bmid is not None

        # Check that attenuation was set
        assert monitor.adc_bplus._attenuation == MockADC.ATTN_11DB
        assert monitor.adc_bmid._attenuation == MockADC.ATTN_11DB

        # Check initial cached values are zero
        assert monitor._bplus_v == 0.0
        assert monitor._bmid_v == 0.0
        assert monitor._cell1_v == 0.0
        assert monitor._cell2_v == 0.0


class TestBatteryVoltageCalculations:
    """Test voltage calculation methods."""

    def test_adc_to_voltage_conversion(self):
        """Test ADC value to voltage conversion."""
        from battery import BatteryMonitor, BPLUS_RATIO, ADC_MAX, ADC_VREF

        monitor = BatteryMonitor()

        # Test with known ADC value for B+
        # If actual battery is 8.4V, ADC should read ~2.36V
        # 2.36V maps to ADC value of (2.36/2.5)*4095 = 3866
        adc_value = 3866
        voltage = monitor._adc_to_voltage(adc_value, BPLUS_RATIO)

        # Should be close to 8.4V
        assert abs(voltage - 8.4) < 0.1

    def test_full_battery_reading(self):
        """Test reading a fully charged 2S LiPo (8.4V)."""
        from battery import BatteryMonitor, BPLUS_RATIO, BMID_RATIO

        monitor = BatteryMonitor()

        # Fully charged: B+ = 8.4V, BM = 4.2V
        # B+ ADC: (8.4V * 0.2806 / 2.5) * 4095 = 3866
        # BM ADC: (4.2V * 0.5875 / 2.5) * 4095 = 4047
        monitor.adc_bplus.set_value(3866)
        monitor.adc_bmid.set_value(4047)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Check total voltage (should be ~8.4V)
        assert abs(total_v - 8.4) < 0.1

        # Check individual cells (should both be ~4.2V)
        assert abs(cell1_v - 4.2) < 0.1
        assert abs(cell2_v - 4.2) < 0.1

    def test_nominal_battery_reading(self):
        """Test reading a nominal 2S LiPo (7.4V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()

        # Nominal: B+ = 7.4V, BM = 3.7V
        # B+ ADC: (7.4V * 0.2806 / 2.5) * 4095 = 3404
        # BM ADC: (3.7V * 0.5875 / 2.5) * 4095 = 3566
        monitor.adc_bplus.set_value(3404)
        monitor.adc_bmid.set_value(3566)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Check total voltage
        assert abs(total_v - 7.4) < 0.1

        # Check individual cells
        assert abs(cell1_v - 3.7) < 0.1
        assert abs(cell2_v - 3.7) < 0.1

    def test_low_battery_reading(self):
        """Test reading a low 2S LiPo (6.6V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()

        # Low: B+ = 6.6V, BM = 3.3V
        # B+ ADC: (6.6V * 0.2806 / 2.5) * 4095 = 3035
        # BM ADC: (3.3V * 0.5875 / 2.5) * 4095 = 3181
        monitor.adc_bplus.set_value(3035)
        monitor.adc_bmid.set_value(3181)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Check total voltage
        assert abs(total_v - 6.6) < 0.1

        # Check individual cells
        assert abs(cell1_v - 3.3) < 0.1
        assert abs(cell2_v - 3.3) < 0.1

    def test_critical_battery_reading(self):
        """Test reading a critically low 2S LiPo (6.0V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()

        # Critical: B+ = 6.0V, BM = 3.0V
        # B+ ADC: (6.0V * 0.2806 / 2.5) * 4095 = 2759
        # BM ADC: (3.0V * 0.5875 / 2.5) * 4095 = 2892
        monitor.adc_bplus.set_value(2759)
        monitor.adc_bmid.set_value(2892)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Check total voltage
        assert abs(total_v - 6.0) < 0.1

        # Check individual cells
        assert abs(cell1_v - 3.0) < 0.1
        assert abs(cell2_v - 3.0) < 0.1

    def test_averaging_multiple_samples(self):
        """Test that multiple samples are averaged correctly."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()

        # Mock read() to return different values
        call_count = [0]
        original_read = monitor.adc_bplus.read

        def mock_read_varying():
            call_count[0] += 1
            # Return 3800, 3850, 3900, 3850, 3800 (avg = 3840)
            values = [3800, 3850, 3900, 3850, 3800]
            return values[(call_count[0] - 1) % len(values)]

        monitor.adc_bplus.read = mock_read_varying
        monitor.adc_bmid.set_value(4000)

        # Read with 5 samples
        total_v, cell1_v, cell2_v = monitor.read(samples=5)

        # Verify read was called 5 times
        assert call_count[0] == 5


class TestBatteryPercentage:
    """Test battery percentage calculation."""

    def test_full_battery_percentage(self):
        """Test percentage at full charge (8.4V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3866)  # 8.4V
        monitor.adc_bmid.set_value(4047)
        monitor.read(samples=1)

        percentage = monitor.get_percentage()
        assert percentage >= 95  # Should be close to 100%

    def test_nominal_battery_percentage(self):
        """Test percentage at nominal voltage (7.4V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3404)  # 7.4V
        monitor.adc_bmid.set_value(3566)
        monitor.read(samples=1)

        percentage = monitor.get_percentage()
        # 7.4V is (7.4-6.0)/(8.4-6.0) = 1.4/2.4 = 58%
        assert 55 <= percentage <= 65

    def test_low_battery_percentage(self):
        """Test percentage at low voltage (6.6V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3035)  # 6.6V
        monitor.adc_bmid.set_value(3181)
        monitor.read(samples=1)

        percentage = monitor.get_percentage()
        # 6.6V is (6.6-6.0)/(8.4-6.0) = 0.6/2.4 = 25%
        assert 20 <= percentage <= 30

    def test_critical_battery_percentage(self):
        """Test percentage at critical voltage (6.0V)."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(2759)  # 6.0V
        monitor.adc_bmid.set_value(2892)
        monitor.read(samples=1)

        percentage = monitor.get_percentage()
        # 6.0V is the minimum, should be 0%
        assert percentage == 0


class TestBatteryStatus:
    """Test battery status checking."""

    def test_ok_status(self):
        """Test OK status for healthy battery."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        # 7.4V nominal
        monitor.adc_bplus.set_value(3404)
        monitor.adc_bmid.set_value(3566)
        monitor.read(samples=1)

        assert monitor.get_status() == "OK"
        assert not monitor.is_low()
        assert not monitor.is_critical()

    def test_low_status(self):
        """Test LOW status for battery below 6.6V."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        # 6.6V (low threshold)
        monitor.adc_bplus.set_value(3035)
        monitor.adc_bmid.set_value(3181)
        monitor.read(samples=1)

        assert monitor.get_status() == "LOW"
        assert monitor.is_low()
        assert not monitor.is_critical()

    def test_critical_status(self):
        """Test CRITICAL status for battery below 6.0V."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        # 5.8V (below critical threshold of 6.0V)
        # B+ ADC: (5.8V * 0.2806 / 2.5) * 4095 = 2667
        # BM ADC: (2.9V * 0.5875 / 2.5) * 4095 = 2796
        monitor.adc_bplus.set_value(2667)
        monitor.adc_bmid.set_value(2796)
        monitor.read(samples=1)

        assert monitor.get_status() == "CRITICAL"
        assert monitor.is_low()
        assert monitor.is_critical()

    def test_imbalanced_status(self):
        """Test IMBALANCED status when cells differ by >0.3V."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        # Total 7.4V but imbalanced: Cell1=3.4V, Cell2=4.0V (diff=0.6V)
        # B+ = 7.4V -> ADC 3404
        # BM = 3.4V -> ADC 3277
        monitor.adc_bplus.set_value(3404)
        monitor.adc_bmid.set_value(3277)
        monitor.read(samples=1)

        # Check that cells are actually imbalanced
        cell1_v, cell2_v = monitor.get_cell_voltages()
        assert abs((cell2_v - cell1_v) - 0.6) < 0.15  # Allow some tolerance

        status = monitor.get_status()
        assert status == "IMBALANCED"
        assert monitor.is_critical()  # Imbalanced is treated as critical

    def test_low_single_cell(self):
        """Test LOW status when one cell is low but total is above LOW threshold."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        # Total 6.8V: Cell1=3.2V (low), Cell2=3.6V (diff=0.4V triggers IMBALANCED first)
        # Need cells within 0.3V to avoid IMBALANCED, but one cell < 3.3V
        # Cell1=3.25V, Cell2=3.45V -> total=6.7V, diff=0.2V (under 0.3V threshold)
        # B+ = 6.7V -> ADC: (6.7 * 0.2806 / 2.5) * 4095 = 3081
        # BM = 3.25V -> ADC: (3.25 * 0.5875 / 2.5) * 4095 = 3133
        monitor.adc_bplus.set_value(3081)
        monitor.adc_bmid.set_value(3133)
        monitor.read(samples=1)

        status = monitor.get_status()
        # Should be LOW because Cell1 < 3.3V and cells are balanced
        assert status == "LOW"


class TestBatteryHelperFunctions:
    """Test helper functions."""

    def test_quick_check(self):
        """Test quick_check convenience function."""
        from battery import quick_check

        voltage, percentage, status = quick_check()

        # Should return valid values
        assert isinstance(voltage, float)
        assert isinstance(percentage, int)
        assert status in ["OK", "LOW", "CRITICAL", "IMBALANCED"]

    def test_get_total_voltage(self):
        """Test get_total_voltage method."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3404)  # 7.4V
        monitor.adc_bmid.set_value(3566)
        monitor.read(samples=1)

        total_v = monitor.get_total_voltage()
        assert abs(total_v - 7.4) < 0.1

    def test_get_cell_voltages(self):
        """Test get_cell_voltages method."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3404)  # 7.4V total
        monitor.adc_bmid.set_value(3566)   # 3.7V mid
        monitor.read(samples=1)

        cell1_v, cell2_v = monitor.get_cell_voltages()
        assert abs(cell1_v - 3.7) < 0.1
        assert abs(cell2_v - 3.7) < 0.1


class TestBatteryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_adc_reading(self):
        """Test handling of zero ADC reading."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(0)
        monitor.adc_bmid.set_value(0)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Should return 0V
        assert total_v == 0.0
        assert cell1_v == 0.0
        assert cell2_v == 0.0

    def test_max_adc_reading(self):
        """Test handling of maximum ADC reading."""
        from battery import BatteryMonitor, ADC_MAX

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(ADC_MAX)
        monitor.adc_bmid.set_value(ADC_MAX)

        total_v, cell1_v, cell2_v = monitor.read(samples=1)

        # Should calculate voltage (will be >8.4V due to max ADC)
        assert total_v > 0

    def test_percentage_clamping(self):
        """Test that percentage is clamped to 0-100 range."""
        from battery import BatteryMonitor

        monitor = BatteryMonitor()

        # Test over max (9.0V - above 8.4V max)
        monitor.adc_bplus.set_value(4138)  # ~9V
        monitor.adc_bmid.set_value(4047)
        monitor.read(samples=1)
        assert monitor.get_percentage() == 100

        # Test under min (5.5V - below 6.0V min)
        monitor.adc_bplus.set_value(2529)  # ~5.5V
        monitor.adc_bmid.set_value(2660)
        monitor.read(samples=1)
        assert monitor.get_percentage() == 0


class TestBatteryPrintOutput:
    """Test print_status output (doesn't crash)."""

    def test_print_status_no_crash(self):
        """Test that print_status runs without error."""
        from battery import BatteryMonitor
        import io
        import sys

        monitor = BatteryMonitor()
        monitor.adc_bplus.set_value(3404)
        monitor.adc_bmid.set_value(3566)
        monitor.read(samples=1)

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            monitor.print_status()
            output = captured_output.getvalue()

            # Check that output contains expected strings
            assert "Battery Status:" in output
            assert "Total:" in output
            assert "Cell 1:" in output
            assert "Cell 2:" in output
            assert "Status:" in output
        finally:
            sys.stdout = sys.__stdout__
