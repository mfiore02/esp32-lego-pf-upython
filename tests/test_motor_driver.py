"""
Unit tests for Motor Driver module

Run with: python -m pytest tests/test_motor_driver.py -v
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


class MockPWM:
    """Mock PWM class for testing."""

    def __init__(self, pin, freq=1000, duty=0):
        self.pin = pin
        self._freq = freq
        self._duty = duty

    def freq(self, val=None):
        """Get or set frequency."""
        if val is not None:
            self._freq = val
        return self._freq

    def duty(self, val=None):
        """Get or set duty cycle."""
        if val is not None:
            self._duty = val
        return self._duty


class MockPin:
    """Mock Pin class for testing."""

    def __init__(self, pin_num, mode=None):
        self.pin_num = pin_num
        self.mode = mode
        self._value = 0

    def value(self, val=None):
        """Get or set pin value."""
        if val is not None:
            self._value = val
        return self._value


class TestMotorDriver:
    """Test single motor driver."""

    def test_initialization(self):
        """Test motor driver initializes to stopped state."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)

        # Should be in brake mode (safer default)
        assert motor.get_speed() == 0
        assert motor.get_mode() == MotorMode.BRAKE
        assert in1.value() == 1
        assert in2.value() == 1
        assert pwm.duty() == 1023

    def test_forward_motion(self):
        """Test forward motion."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(50, MotorMode.FORWARD)

        # Check direction pins
        assert in1.value() == 1
        assert in2.value() == 0

        # Check speed (50% = 511.5 ≈ 511)
        duty = pwm.duty()
        assert 510 <= duty <= 512

        assert motor.get_speed() == 50
        assert motor.get_mode() == MotorMode.FORWARD

    def test_reverse_motion(self):
        """Test reverse motion."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(75, MotorMode.REVERSE)

        # Check direction pins
        assert in1.value() == 0
        assert in2.value() == 1

        # Check speed (75% = 767.25 ≈ 767)
        duty = pwm.duty()
        assert 766 <= duty <= 768

        assert motor.get_speed() == 75
        assert motor.get_mode() == MotorMode.REVERSE

    def test_brake_stop(self):
        """Test brake stop."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(50, MotorMode.FORWARD)
        motor.stop(brake=True)

        # Brake: IN1=1, IN2=1, PWM=max
        assert in1.value() == 1
        assert in2.value() == 1
        assert pwm.duty() == 1023

        assert motor.get_speed() == 0
        assert motor.get_mode() == MotorMode.BRAKE

    def test_coast_stop(self):
        """Test coast stop."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(50, MotorMode.FORWARD)
        motor.stop(brake=False)

        # Coast: IN1=0, IN2=0, PWM=0
        assert in1.value() == 0
        assert in2.value() == 0
        assert pwm.duty() == 0

        assert motor.get_speed() == 0
        assert motor.get_mode() == MotorMode.COAST

    def test_speed_clamping_max(self):
        """Test speed clamping at maximum."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(150, MotorMode.FORWARD)  # Over 100

        assert motor.get_speed() == 100
        assert pwm.duty() == 1023  # Max PWM

    def test_speed_clamping_min(self):
        """Test speed clamping at minimum."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(-50, MotorMode.FORWARD)  # Negative

        assert motor.get_speed() == 0
        # Should coast when speed is 0
        assert in1.value() == 0
        assert in2.value() == 0

    def test_zero_speed_coasts(self):
        """Test that zero speed results in coast."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(0, MotorMode.FORWARD)

        # Zero speed should coast
        assert in1.value() == 0
        assert in2.value() == 0
        assert pwm.duty() == 0

    def test_reverse_motor_configuration(self):
        """Test motor reversal configuration."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2, reverse=True)
        motor.drive(50, MotorMode.FORWARD)

        # With reverse=True, forward command should drive reverse
        assert in1.value() == 0
        assert in2.value() == 1

        # Now try reverse with reverse=True
        motor.drive(50, MotorMode.REVERSE)

        # Should drive forward
        assert in1.value() == 1
        assert in2.value() == 0

    def test_deadband(self):
        """Test deadband functionality."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2, deadband=10)

        # Speed below deadband should result in 0
        motor.drive(5, MotorMode.FORWARD)
        assert motor.get_speed() == 0

        # Speed at deadband edge should pass through (uses < not <=)
        motor.drive(9, MotorMode.FORWARD)
        assert motor.get_speed() == 0

        # Speed at or above deadband should work
        motor.drive(10, MotorMode.FORWARD)
        assert motor.get_speed() == 10
        assert pwm.duty() > 0

        motor.drive(11, MotorMode.FORWARD)
        assert motor.get_speed() == 11
        assert pwm.duty() > 0

    def test_set_deadband(self):
        """Test setting deadband after initialization."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.set_deadband(15)

        motor.drive(10, MotorMode.FORWARD)
        assert motor.get_speed() == 0

        motor.drive(20, MotorMode.FORWARD)
        assert motor.get_speed() == 20

    def test_set_reverse(self):
        """Test setting reverse after initialization."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)
        motor.drive(50, MotorMode.FORWARD)

        # Normal forward
        assert in1.value() == 1
        assert in2.value() == 0

        # Enable reverse
        motor.set_reverse(True)
        motor.drive(50, MotorMode.FORWARD)

        # Should now be reversed
        assert in1.value() == 0
        assert in2.value() == 1

    def test_full_speed_range(self):
        """Test full speed range 0-100."""
        from motor_driver import MotorDriver, MotorMode

        pwm = MockPWM(None)
        in1 = MockPin(1)
        in2 = MockPin(2)

        motor = MotorDriver(pwm, in1, in2)

        # Test several points
        test_speeds = [0, 25, 50, 75, 100]

        for speed in test_speeds:
            motor.drive(speed, MotorMode.FORWARD)
            assert motor.get_speed() == speed

            expected_duty = int((speed * 1023) / 100)
            actual_duty = pwm.duty()

            # Allow small rounding tolerance
            if speed == 0:
                assert actual_duty == 0
            else:
                assert abs(actual_duty - expected_duty) <= 1


class TestDualMotorDriver:
    """Test dual motor driver."""

    def test_initialization(self):
        """Test dual motor driver initialization."""
        from motor_driver import MotorDriver, DualMotorDriver

        pwm1 = MockPWM(None)
        in1_1 = MockPin(1)
        in2_1 = MockPin(2)
        motor1 = MotorDriver(pwm1, in1_1, in2_1)

        pwm2 = MockPWM(None)
        in1_2 = MockPin(3)
        in2_2 = MockPin(4)
        motor2 = MotorDriver(pwm2, in1_2, in2_2)

        dual = DualMotorDriver(motor1, motor2)

        assert dual.motor1 is motor1
        assert dual.motor2 is motor2

    def test_drive_both(self):
        """Test driving both motors together."""
        from motor_driver import MotorDriver, DualMotorDriver, MotorMode

        pwm1 = MockPWM(None)
        in1_1 = MockPin(1)
        in2_1 = MockPin(2)
        motor1 = MotorDriver(pwm1, in1_1, in2_1)

        pwm2 = MockPWM(None)
        in1_2 = MockPin(3)
        in2_2 = MockPin(4)
        motor2 = MotorDriver(pwm2, in1_2, in2_2)

        dual = DualMotorDriver(motor1, motor2)
        dual.drive_both(60, MotorMode.FORWARD)

        # Both motors should be running forward at 60%
        assert motor1.get_speed() == 60
        assert motor1.get_mode() == MotorMode.FORWARD
        assert motor2.get_speed() == 60
        assert motor2.get_mode() == MotorMode.FORWARD

    def test_drive_independent(self):
        """Test driving motors independently."""
        from motor_driver import MotorDriver, DualMotorDriver, MotorMode

        pwm1 = MockPWM(None)
        in1_1 = MockPin(1)
        in2_1 = MockPin(2)
        motor1 = MotorDriver(pwm1, in1_1, in2_1)

        pwm2 = MockPWM(None)
        in1_2 = MockPin(3)
        in2_2 = MockPin(4)
        motor2 = MotorDriver(pwm2, in1_2, in2_2)

        dual = DualMotorDriver(motor1, motor2)
        dual.drive_independent(40, MotorMode.FORWARD, 80, MotorMode.REVERSE)

        # Motor 1 forward at 40%
        assert motor1.get_speed() == 40
        assert motor1.get_mode() == MotorMode.FORWARD

        # Motor 2 reverse at 80%
        assert motor2.get_speed() == 80
        assert motor2.get_mode() == MotorMode.REVERSE

    def test_stop_both(self):
        """Test stopping both motors."""
        from motor_driver import MotorDriver, DualMotorDriver, MotorMode

        pwm1 = MockPWM(None)
        in1_1 = MockPin(1)
        in2_1 = MockPin(2)
        motor1 = MotorDriver(pwm1, in1_1, in2_1)

        pwm2 = MockPWM(None)
        in1_2 = MockPin(3)
        in2_2 = MockPin(4)
        motor2 = MotorDriver(pwm2, in1_2, in2_2)

        dual = DualMotorDriver(motor1, motor2)
        dual.drive_both(50, MotorMode.FORWARD)
        dual.stop_both(brake=True)

        # Both should be braking
        assert motor1.get_speed() == 0
        assert motor1.get_mode() == MotorMode.BRAKE
        assert motor2.get_speed() == 0
        assert motor2.get_mode() == MotorMode.BRAKE


print("Motor driver tests created successfully")
