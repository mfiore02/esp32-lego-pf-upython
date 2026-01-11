"""
Hardware-in-Loop Test for Motor Driver Module

This script tests the TB6612FNG motor driver on actual ESP32 hardware.

To run:
    1. Flash to device:
       mpremote connect COM3 fs cp hwil/test_motor_driver_hwil.py :main.py
       mpremote connect COM3 fs cp lib/motor_driver.py :lib/motor_driver.py

    2. Monitor output:
       mpremote connect COM3 repl

Expected behavior:
    - Motors run forward, reverse, stop
    - Speed ramps up and down
    - Tests both motor channels

Hardware setup:
    See lib/hardware.py for GPIO pin assignments.
    - TB6612FNG motor driver connected to ESP32
    - Motor 1: PWM=GPIO2, IN1=GPIO3, IN2=GPIO4
    - Motor 2: PWM=GPIO5, IN1=GPIO6, IN2=GPIO7
    - Connect STBY pin to 3.3V (always enabled)
    - VCC to 3.3V, VM to motor power supply (2S LiPo ~7.4V)
    - Connect 2x DC motors to A01/A02 and B01/B02

WARNING: Ensure motors are properly secured before running tests!
"""

import sys
import time
from machine import Pin, PWM

# Add lib to path if needed
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from motor_driver import MotorDriver, DualMotorDriver, MotorMode
import hardware


def test_single_motor():
    """Test single motor through all modes."""

    print("\n" + "="*50)
    print("Single Motor Test")
    print("="*50)

    # Configure Motor 1 - from hardware config
    print("Configuring Motor 1...")
    print("  PWM={}, IN1={}, IN2={}".format(
        hardware.MOTOR1_PWM_GPIO, hardware.MOTOR1_IN1_GPIO, hardware.MOTOR1_IN2_GPIO))
    pwm1 = PWM(Pin(hardware.MOTOR1_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_1 = Pin(hardware.MOTOR1_IN1_GPIO, Pin.OUT)
    in2_1 = Pin(hardware.MOTOR1_IN2_GPIO, Pin.OUT)

    motor1 = MotorDriver(pwm1, in1_1, in2_1)

    print("Motor configured")
    print("\nWARNING: Motor will start moving!")
    print("Press Ctrl+C to stop at any time\n")
    time.sleep(2)

    try:
        # Test forward
        print("[1/6] Testing FORWARD at 50%...")
        motor1.drive(50, MotorMode.FORWARD)
        time.sleep(2)

        # Test faster forward
        print("[2/6] Testing FORWARD at 75%...")
        motor1.drive(75, MotorMode.FORWARD)
        time.sleep(2)

        # Test max forward
        print("[3/6] Testing FORWARD at 100%...")
        motor1.drive(100, MotorMode.FORWARD)
        time.sleep(2)

        # Stop with brake
        print("[4/6] Testing BRAKE...")
        motor1.stop(brake=True)
        time.sleep(2)

        # Test reverse
        print("[5/6] Testing REVERSE at 50%...")
        motor1.drive(50, MotorMode.REVERSE)
        time.sleep(2)

        # Coast stop
        print("[6/6] Testing COAST...")
        motor1.stop(brake=False)
        time.sleep(1)

        print("\nSingle motor test complete!")

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")

    finally:
        motor1.stop(brake=True)
        print("Motor stopped (brake)")


def test_speed_ramp():
    """Test motor speed ramping."""

    print("\n" + "="*50)
    print("Speed Ramp Test")
    print("="*50)

    print("Configuring Motor 1...")
    pwm1 = PWM(Pin(hardware.MOTOR1_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_1 = Pin(hardware.MOTOR1_IN1_GPIO, Pin.OUT)
    in2_1 = Pin(hardware.MOTOR1_IN2_GPIO, Pin.OUT)

    motor1 = MotorDriver(pwm1, in1_1, in2_1)

    print("\nRamping speed from 0 to 100% in forward")
    print("Press Ctrl+C to stop\n")
    time.sleep(1)

    try:
        # Ramp up forward
        for speed in range(0, 101, 10):
            print("Speed: {}%".format(speed))
            motor1.drive(speed, MotorMode.FORWARD)
            time.sleep(0.5)

        time.sleep(1)

        # Ramp down
        print("\nRamping down...")
        for speed in range(100, -1, -10):
            print("Speed: {}%".format(speed))
            motor1.drive(speed, MotorMode.FORWARD)
            time.sleep(0.5)

        print("\nRamp test complete!")

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")

    finally:
        motor1.stop(brake=True)
        print("Motor stopped")


def test_dual_motors():
    """Test both motors together."""

    print("\n" + "="*50)
    print("Dual Motor Test")
    print("="*50)

    print("Configuring Motor 1 and Motor 2...")

    # Motor 1 - from hardware config
    pwm1 = PWM(Pin(hardware.MOTOR1_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_1 = Pin(hardware.MOTOR1_IN1_GPIO, Pin.OUT)
    in2_1 = Pin(hardware.MOTOR1_IN2_GPIO, Pin.OUT)
    motor1 = MotorDriver(pwm1, in1_1, in2_1)

    # Motor 2 - from hardware config
    pwm2 = PWM(Pin(hardware.MOTOR2_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_2 = Pin(hardware.MOTOR2_IN1_GPIO, Pin.OUT)
    in2_2 = Pin(hardware.MOTOR2_IN2_GPIO, Pin.OUT)
    motor2 = MotorDriver(pwm2, in1_2, in2_2)

    dual = DualMotorDriver(motor1, motor2)

    print("Motors configured")
    print("\nWARNING: Both motors will start moving!")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)

    try:
        # Both forward
        print("[1/4] Both motors FORWARD at 60%...")
        dual.drive_both(60, MotorMode.FORWARD)
        time.sleep(3)

        # Both reverse
        print("[2/4] Both motors REVERSE at 60%...")
        dual.drive_both(60, MotorMode.REVERSE)
        time.sleep(3)

        # Independent - Motor 1 forward, Motor 2 reverse
        print("[3/4] Motor 1 FORWARD 50%, Motor 2 REVERSE 50%...")
        dual.drive_independent(50, MotorMode.FORWARD, 50, MotorMode.REVERSE)
        time.sleep(3)

        # Reverse roles
        print("[4/4] Motor 1 REVERSE 50%, Motor 2 FORWARD 50%...")
        dual.drive_independent(50, MotorMode.REVERSE, 50, MotorMode.FORWARD)
        time.sleep(3)

        print("\nDual motor test complete!")

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")

    finally:
        dual.stop_both(brake=True)
        print("Both motors stopped")


def test_motor_reversal():
    """Test motor direction reversal feature."""

    print("\n" + "="*50)
    print("Motor Reversal Test")
    print("="*50)

    print("Configuring Motor 1...")
    pwm1 = PWM(Pin(hardware.MOTOR1_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_1 = Pin(hardware.MOTOR1_IN1_GPIO, Pin.OUT)
    in2_1 = Pin(hardware.MOTOR1_IN2_GPIO, Pin.OUT)

    motor1 = MotorDriver(pwm1, in1_1, in2_1)

    print("\nTesting direction reversal feature")
    print("Press Ctrl+C to stop\n")
    time.sleep(1)

    try:
        # Normal forward
        print("[1/4] FORWARD command (normal direction)...")
        motor1.drive(60, MotorMode.FORWARD)
        time.sleep(2)

        motor1.stop(brake=True)
        time.sleep(1)

        # Enable reversal
        print("[2/4] Enabling motor reversal...")
        motor1.set_reverse(True)
        print("[3/4] FORWARD command (reversed - should spin opposite)...")
        motor1.drive(60, MotorMode.FORWARD)
        time.sleep(2)

        motor1.stop(brake=True)
        time.sleep(1)

        # Disable reversal
        print("[4/4] Disabling reversal, back to normal...")
        motor1.set_reverse(False)
        motor1.drive(60, MotorMode.FORWARD)
        time.sleep(2)

        print("\nReversal test complete!")

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")

    finally:
        motor1.stop(brake=True)
        print("Motor stopped")


def test_interactive():
    """
    Interactive motor test - use REPL to control motors.

    Provides motor objects in global scope for manual control.
    """

    print("\n" + "="*50)
    print("Interactive Motor Test")
    print("="*50)

    print("Configuring motors...")

    # Motor 1 - from hardware config
    pwm1 = PWM(Pin(hardware.MOTOR1_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_1 = Pin(hardware.MOTOR1_IN1_GPIO, Pin.OUT)
    in2_1 = Pin(hardware.MOTOR1_IN2_GPIO, Pin.OUT)
    motor1 = MotorDriver(pwm1, in1_1, in2_1)

    # Motor 2 - from hardware config
    pwm2 = PWM(Pin(hardware.MOTOR2_PWM_GPIO), freq=hardware.MOTOR_PWM_FREQ, duty=0)
    in1_2 = Pin(hardware.MOTOR2_IN1_GPIO, Pin.OUT)
    in2_2 = Pin(hardware.MOTOR2_IN2_GPIO, Pin.OUT)
    motor2 = MotorDriver(pwm2, in1_2, in2_2)

    dual = DualMotorDriver(motor1, motor2)

    print("\nMotors configured for interactive control")
    print("\nAvailable objects:")
    print("  motor1 - Motor 1 controller")
    print("  motor2 - Motor 2 controller")
    print("  dual - Dual motor controller")
    print("  MotorMode - Mode constants")
    print("\nExample commands:")
    print("  motor1.drive(75, MotorMode.FORWARD)")
    print("  motor2.drive(50, MotorMode.REVERSE)")
    print("  motor1.stop(brake=True)")
    print("  dual.drive_both(60, MotorMode.FORWARD)")
    print("  dual.stop_both()")
    print("\nPress Ctrl+C to exit and stop motors")

    # Make available globally for REPL
    globals()['motor1'] = motor1
    globals()['motor2'] = motor2
    globals()['dual'] = dual
    globals()['MotorMode'] = MotorMode

    try:
        # Keep running
        print("\nInteractive mode active...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nExiting interactive mode")
        dual.stop_both(brake=True)
        print("Motors stopped")


# Run single motor test by default
# Uncomment others as needed
if __name__ == "__main__":
    test_single_motor()
    # test_speed_ramp()
    # test_dual_motors()
    # test_motor_reversal()
    # test_interactive()
