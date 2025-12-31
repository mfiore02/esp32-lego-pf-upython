"""
Potentiometer ADC Module with Dead Zone Calibration

Reads analog input from potentiometer with calibration and dead zone support.
Maps raw ADC values to speed percentage (0-100).

Example usage:
    from machine import Pin, ADC
    from potentiometer import Potentiometer

    # Create potentiometer on GPIO0 (ADC1_CH0)
    adc = ADC(Pin(0))
    adc.atten(ADC.ATTN_11DB)  # Full 0-3.3V range

    pot = Potentiometer(adc, min_val=100, max_val=3995, zero_band=50)

    # In main loop
    while True:
        speed = pot.read()  # Returns 0-100
        print("Speed:", speed, "%")
        time.sleep_ms(100)
"""


class Potentiometer:
    """ADC-based potentiometer reader with calibration and dead zone."""

    def __init__(self, adc, min_val=100, max_val=3995, zero_band=50):
        """
        Initialize potentiometer reader.

        Args:
            adc: machine.ADC object configured for reading
            min_val: Minimum expected ADC value (default: 100)
            max_val: Maximum expected ADC value (default: 3995)
            zero_band: Dead zone size at minimum position in ADC units (default: 50)
        """
        self.adc = adc
        self.min_val = min_val
        self.max_val = max_val
        self.zero_band = zero_band

        # Validate calibration
        if min_val >= max_val:
            raise ValueError("min_val must be less than max_val")
        if zero_band < 0:
            raise ValueError("zero_band must be non-negative")

    def read(self):
        """
        Read potentiometer and return calibrated speed percentage.

        Returns:
            Speed value from 0-100
        """
        raw = self.read_raw()
        return self._map_value(raw)

    def read_raw(self):
        """
        Read raw ADC value.

        Returns:
            Raw ADC value (typically 0-4095 for 12-bit ADC)
        """
        return self.adc.read()

    def set_calibration(self, min_val, max_val, zero_band):
        """
        Update calibration parameters.

        Args:
            min_val: Minimum expected ADC value
            max_val: Maximum expected ADC value
            zero_band: Dead zone size at minimum position
        """
        if min_val >= max_val:
            raise ValueError("min_val must be less than max_val")
        if zero_band < 0:
            raise ValueError("zero_band must be non-negative")

        self.min_val = min_val
        self.max_val = max_val
        self.zero_band = zero_band

    def get_calibration(self):
        """
        Get current calibration parameters.

        Returns:
            Tuple of (min_val, max_val, zero_band)
        """
        return (self.min_val, self.max_val, self.zero_band)

    def _map_value(self, raw):
        """
        Map raw ADC value to speed percentage with dead zone.

        Args:
            raw: Raw ADC reading

        Returns:
            Speed value from 0-100
        """
        # Clamp to calibrated range
        if raw <= self.min_val:
            raw = self.min_val
        elif raw >= self.max_val:
            raw = self.max_val

        # Apply zero band at minimum position
        # If within zero_band of min_val, return 0
        if raw < (self.min_val + self.zero_band):
            return 0

        # Map to 0-100 range
        # Adjust min to account for zero band
        adjusted_min = self.min_val + self.zero_band
        usable_range = self.max_val - adjusted_min

        # Calculate percentage
        speed = int(((raw - adjusted_min) * 100) / usable_range)

        # Ensure result is in valid range
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100

        return speed
