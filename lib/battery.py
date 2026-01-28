"""
Battery Monitoring Module for 2S LiPo

Reads battery voltages through hardware voltage dividers and provides
battery status information.

Hardware:
- B+ (full battery): GPIO0, 100k/39k divider (8.4V → 2.36V max)
- BM (mid-point):   GPIO1, 33k/47k divider (4.2V → 2.47V max)
- ADC range: 0-2.5V with ATTN_11DB, 12-bit resolution (0-4095)

See kicad/receiver_board_power schematic for voltage divider details.
"""

from machine import ADC, Pin
import hardware


# ============================================================================
# VOLTAGE DIVIDER CONSTANTS
# ============================================================================

# B+ divider: R1=100k (top), R2=39k (bottom to GND)
# Vout = Vin × (R2 / (R1 + R2))
BPLUS_R1 = 100000  # 100k ohms
BPLUS_R2 = 39000   # 39k ohms
BPLUS_RATIO = BPLUS_R2 / (BPLUS_R1 + BPLUS_R2)  # 0.2806

# BM divider: R3=33k (top), R4=47k (bottom to GND)
BMID_R1 = 33000    # 33k ohms
BMID_R2 = 47000    # 47k ohms
BMID_RATIO = BMID_R2 / (BMID_R1 + BMID_R2)  # 0.5875

# ADC Configuration
ADC_MAX = 4095          # 12-bit ADC
ADC_VREF = 2.5          # Reference voltage at ATTN_11DB (0-2.5V range)

# LiPo Cell Voltage Thresholds (per cell)
CELL_MAX_V = 4.2        # Fully charged
CELL_NOM_V = 3.7        # Nominal
CELL_LOW_V = 3.3        # Low battery warning
CELL_MIN_V = 3.0        # Critical - stop using immediately

# 2S Battery Thresholds (total voltage)
BATTERY_MAX_V = 8.4     # 2S fully charged
BATTERY_NOM_V = 7.4     # 2S nominal
BATTERY_LOW_V = 6.6     # 2S low warning
BATTERY_MIN_V = 6.0     # 2S critical


# ============================================================================
# BATTERY MONITOR CLASS
# ============================================================================

class BatteryMonitor:
    """Monitor 2S LiPo battery voltage through hardware dividers."""

    def __init__(self):
        """Initialize ADC channels for battery monitoring."""
        # Initialize ADC pins
        self.adc_bplus = ADC(Pin(hardware.BATTERY_BPLUS_GPIO))
        self.adc_bmid = ADC(Pin(hardware.BATTERY_BMID_GPIO))

        # Set attenuation for 0-2.5V range
        self.adc_bplus.atten(ADC.ATTN_11DB)
        self.adc_bmid.atten(ADC.ATTN_11DB)

        # Cached readings
        self._bplus_v = 0.0
        self._bmid_v = 0.0
        self._cell1_v = 0.0
        self._cell2_v = 0.0

    def _adc_to_voltage(self, adc_value, divider_ratio):
        """
        Convert ADC reading to actual voltage.

        Args:
            adc_value: Raw ADC reading (0-4095)
            divider_ratio: Voltage divider ratio (Vout/Vin)

        Returns:
            Actual voltage at the battery
        """
        # Convert ADC to voltage at ADC pin
        adc_voltage = (adc_value / ADC_MAX) * ADC_VREF

        # Scale back through divider to get actual battery voltage
        actual_voltage = adc_voltage / divider_ratio

        return actual_voltage

    def read(self, samples=10):
        """
        Read battery voltages with averaging.

        Args:
            samples: Number of samples to average (default 10)

        Returns:
            Tuple of (total_voltage, cell1_voltage, cell2_voltage)
        """
        # Accumulate samples
        bplus_sum = 0
        bmid_sum = 0

        for _ in range(samples):
            bplus_sum += self.adc_bplus.read()
            bmid_sum += self.adc_bmid.read()

        # Average the samples
        bplus_avg = bplus_sum / samples
        bmid_avg = bmid_sum / samples

        # Convert to actual voltages
        self._bplus_v = self._adc_to_voltage(bplus_avg, BPLUS_RATIO)
        self._bmid_v = self._adc_to_voltage(bmid_avg, BMID_RATIO)

        # Calculate individual cell voltages
        # Cell 1 is from GND to BM (mid-point)
        # Cell 2 is from BM to B+ (top)
        self._cell1_v = self._bmid_v
        self._cell2_v = self._bplus_v - self._bmid_v

        return (self._bplus_v, self._cell1_v, self._cell2_v)

    def get_total_voltage(self):
        """Get total battery voltage (B+)."""
        return self._bplus_v

    def get_cell_voltages(self):
        """Get individual cell voltages as (cell1, cell2)."""
        return (self._cell1_v, self._cell2_v)

    def get_percentage(self):
        """
        Estimate battery percentage based on total voltage.

        Uses a simple linear approximation between nominal and max voltage.
        Not perfectly accurate for LiPo discharge curve, but reasonable.

        Returns:
            Battery percentage (0-100)
        """
        # Clamp voltage to valid range
        v = max(BATTERY_MIN_V, min(self._bplus_v, BATTERY_MAX_V))

        # Linear interpolation between min and max
        percentage = ((v - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100

        return int(percentage)

    def get_status(self):
        """
        Get battery status string.

        Returns:
            Status: "OK", "LOW", "CRITICAL", or "IMBALANCED"
        """
        # Check for cell imbalance (>0.3V difference is concerning)
        if abs(self._cell1_v - self._cell2_v) > 0.3:
            return "IMBALANCED"

        # Check total voltage
        if self._bplus_v < BATTERY_MIN_V:
            return "CRITICAL"
        elif self._bplus_v < BATTERY_LOW_V:
            return "LOW"

        # Check individual cells
        if self._cell1_v < CELL_MIN_V or self._cell2_v < CELL_MIN_V:
            return "CRITICAL"
        elif self._cell1_v < CELL_LOW_V or self._cell2_v < CELL_LOW_V:
            return "LOW"

        return "OK"

    def is_low(self):
        """Check if battery is low."""
        status = self.get_status()
        return status in ("LOW", "CRITICAL", "IMBALANCED")

    def is_critical(self):
        """Check if battery is critically low."""
        status = self.get_status()
        return status in ("CRITICAL", "IMBALANCED")

    def print_status(self):
        """Print formatted battery status to console."""
        print("Battery Status:")
        print(f"  Total:  {self._bplus_v:.2f}V ({self.get_percentage()}%)")
        print(f"  Cell 1: {self._cell1_v:.2f}V")
        print(f"  Cell 2: {self._cell2_v:.2f}V")
        print(f"  Status: {self.get_status()}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_check():
    """
    Perform a quick battery check and return status.

    Returns:
        Tuple of (voltage, percentage, status_string)
    """
    monitor = BatteryMonitor()
    total_v, cell1_v, cell2_v = monitor.read()
    percentage = monitor.get_percentage()
    status = monitor.get_status()

    return (total_v, percentage, status)


def test():
    """Test battery monitoring and print detailed output."""
    print("Initializing battery monitor...")
    monitor = BatteryMonitor()

    print("\nReading battery (averaging 20 samples)...")
    monitor.read(samples=20)

    print()
    monitor.print_status()

    return monitor
