"""
ESP32-C3 Hardware Configuration

Centralized GPIO pin assignments and hardware constants for both
controller and receiver devices.

See main README.md for complete hardware documentation.
"""

# ============================================================================
# SHARED I/O (Both Controller and Receiver)
# ============================================================================

LED_GPIO = 8            # Status LED (active high)
BUTTON_GPIO = 10        # Pairing/function button (active low with pull-up)

# Hardware Configuration
LED_ACTIVE_HIGH = True
BUTTON_ACTIVE_LOW = True

# Communication
ESPNOW_CHANNEL = 1      # WiFi channel for ESP-NOW


# ============================================================================
# CONTROLLER-SPECIFIC I/O
# ============================================================================

# Potentiometer
POT_GPIO = 1            # Potentiometer ADC input

# ADC Configuration
ADC_BITS = 12           # ESP32-C3 has 12-bit ADC
ADC_MAX = 4095          # Maximum ADC value (2^12 - 1)

# Default Calibration (can be overridden by config)
DEFAULT_POT_MIN = 0
DEFAULT_POT_MAX = 3995
DEFAULT_ZERO_BAND = 100

# Transmit Rate
TX_RATE_HZ = 20         # Transmit rate (20Hz = 50ms period)
TX_PERIOD_MS = 50       # Transmit period in milliseconds


# ============================================================================
# RECEIVER-SPECIFIC I/O
# ============================================================================

# Battery Monitoring (2S LiPo via voltage dividers)
BATTERY_BPLUS_GPIO = 0   # B+ (full battery voltage, 0-8.4V → 0-2.36V via divider)
BATTERY_BMID_GPIO = 1    # BM (mid-point voltage, 0-4.2V → 0-2.47V via divider)

# Motor 1 (Channel A) - TB6612FNG
MOTOR1_PWM_GPIO = 2     # PWMA
MOTOR1_IN1_GPIO = 4     # AIN1
MOTOR1_IN2_GPIO = 3     # AIN2

# Motor 2 (Channel B) - TB6612FNG
MOTOR2_PWM_GPIO = 5     # PWMB
MOTOR2_IN1_GPIO = 7     # BIN1
MOTOR2_IN2_GPIO = 6     # BIN2

# PWM Configuration
MOTOR_PWM_FREQ = 1000   # PWM frequency in Hz (1kHz)
MOTOR_PWM_BITS = 10     # ESP32 PWM resolution (10-bit = 0-1023)
MOTOR_PWM_MAX = 1023    # Maximum PWM duty cycle

# Default Motor Configuration (can be overridden by config)
DEFAULT_DEADBAND = 0
DEFAULT_REVERSE_M1 = False
DEFAULT_REVERSE_M2 = False
DEFAULT_MAX_SPEED = 100

# Safety and Timing
SAFETY_TIMEOUT_MS = 125 # Stop motors if no message for 125ms (2.5x 50ms period)

# LED Blink Rates
PAIRING_BLINK_HZ = 4    # Fast blink during pairing
IDLE_BLINK_HZ = 1       # Slow blink when idle

# Pairing
PAIRING_TIMEOUT_SEC = 30  # Pairing mode timeout
