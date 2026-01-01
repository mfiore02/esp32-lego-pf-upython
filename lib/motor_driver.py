"""
TB6612FNG Dual Motor Driver Module

Controls TB6612FNG dual H-bridge motor driver for driving two DC motors.
Supports forward, reverse, brake, and coast modes with PWM speed control.

Example usage:
    from machine import Pin, PWM
    from motor_driver import MotorDriver, MotorMode

    # Motor 1: PWM on GPIO2, IN1 on GPIO3, IN2 on GPIO10
    pwm1 = PWM(Pin(2), freq=1000, duty=0)
    motor1 = MotorDriver(pwm1, Pin(3, Pin.OUT), Pin(10, Pin.OUT))

    # Run forward at 75% speed
    motor1.drive(75, MotorMode.FORWARD)

    # Stop (brake)
    motor1.stop()

    # Run reverse at 50% speed
    motor1.drive(50, MotorMode.REVERSE)
"""


class MotorMode:
    """Motor operation modes."""

    FORWARD = 0   # IN1=1, IN2=0, PWM=speed
    REVERSE = 1   # IN1=0, IN2=1, PWM=speed
    BRAKE = 2     # IN1=1, IN2=1, PWM=1023 (short brake)
    COAST = 3     # IN1=0, IN2=0, PWM=0 (free spin)


class MotorDriver:
    """TB6612FNG motor driver controller for single motor channel."""

    def __init__(self, pwm, in1_pin, in2_pin, reverse=False, deadband=0):
        """
        Initialize motor driver.

        Args:
            pwm: machine.PWM object for speed control
            in1_pin: machine.Pin object for IN1 (direction control)
            in2_pin: machine.Pin object for IN2 (direction control)
            reverse: Swap forward/reverse direction (default: False)
            deadband: Minimum speed percentage to apply (0-100, default: 0)
        """
        self.pwm = pwm
        self.in1 = in1_pin
        self.in2 = in2_pin
        self.reverse = reverse
        self.deadband = deadband

        # Current state
        self._speed = 0  # Current speed (0-100)
        self._mode = MotorMode.COAST  # Current mode

        # Initialize to stopped state
        self.stop()

    def drive(self, speed, mode=MotorMode.FORWARD):
        """
        Drive motor at specified speed and direction.

        Args:
            speed: Speed percentage (0-100)
            mode: MotorMode.FORWARD or MotorMode.REVERSE
        """
        # Validate speed
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100

        # Apply deadband
        if speed < self.deadband:
            speed = 0

        # Store state
        self._speed = speed
        self._mode = mode

        # Handle reverse motor configuration
        actual_mode = mode
        if self.reverse:
            if mode == MotorMode.FORWARD:
                actual_mode = MotorMode.REVERSE
            elif mode == MotorMode.REVERSE:
                actual_mode = MotorMode.FORWARD

        # Apply mode
        if speed == 0:
            # No speed - coast
            self._set_mode(MotorMode.COAST)
        else:
            # Set direction
            self._set_mode(actual_mode)
            # Set speed (0-1023 for MicroPython PWM)
            duty = int((speed * 1023) / 100)
            self.pwm.duty(duty)

    def stop(self, brake=True):
        """
        Stop motor.

        Args:
            brake: True for active brake, False for coast (default: True)
        """
        self._speed = 0

        if brake:
            self._mode = MotorMode.BRAKE
            self._set_mode(MotorMode.BRAKE)
        else:
            self._mode = MotorMode.COAST
            self._set_mode(MotorMode.COAST)

    def get_speed(self):
        """
        Get current speed.

        Returns:
            Current speed (0-100)
        """
        return self._speed

    def get_mode(self):
        """
        Get current mode.

        Returns:
            Current MotorMode
        """
        return self._mode

    def set_reverse(self, reverse):
        """
        Set motor direction reversal.

        Args:
            reverse: True to reverse motor direction
        """
        self.reverse = reverse

    def set_deadband(self, deadband):
        """
        Set minimum speed threshold.

        Args:
            deadband: Minimum speed percentage (0-100)
        """
        if deadband < 0:
            deadband = 0
        elif deadband > 100:
            deadband = 100

        self.deadband = deadband

    def _set_mode(self, mode):
        """
        Set motor mode using IN1/IN2 pins.

        Args:
            mode: MotorMode constant
        """
        if mode == MotorMode.FORWARD:
            # Forward: IN1=1, IN2=0
            self.in1.value(1)
            self.in2.value(0)

        elif mode == MotorMode.REVERSE:
            # Reverse: IN1=0, IN2=1
            self.in1.value(0)
            self.in2.value(1)

        elif mode == MotorMode.BRAKE:
            # Brake: IN1=1, IN2=1, PWM=high
            self.in1.value(1)
            self.in2.value(1)
            self.pwm.duty(1023)

        elif mode == MotorMode.COAST:
            # Coast: IN1=0, IN2=0, PWM=0
            self.in1.value(0)
            self.in2.value(0)
            self.pwm.duty(0)


class DualMotorDriver:
    """Dual motor driver for controlling two motors with TB6612FNG."""

    def __init__(self, motor1, motor2):
        """
        Initialize dual motor driver.

        Args:
            motor1: MotorDriver instance for motor 1
            motor2: MotorDriver instance for motor 2
        """
        self.motor1 = motor1
        self.motor2 = motor2

    def drive_both(self, speed, mode=MotorMode.FORWARD):
        """
        Drive both motors at same speed and direction.

        Args:
            speed: Speed percentage (0-100)
            mode: MotorMode.FORWARD or MotorMode.REVERSE
        """
        self.motor1.drive(speed, mode)
        self.motor2.drive(speed, mode)

    def drive_independent(self, speed1, mode1, speed2, mode2):
        """
        Drive motors independently.

        Args:
            speed1: Motor 1 speed (0-100)
            mode1: Motor 1 mode
            speed2: Motor 2 speed (0-100)
            mode2: Motor 2 mode
        """
        self.motor1.drive(speed1, mode1)
        self.motor2.drive(speed2, mode2)

    def stop_both(self, brake=True):
        """
        Stop both motors.

        Args:
            brake: True for active brake, False for coast
        """
        self.motor1.stop(brake)
        self.motor2.stop(brake)
