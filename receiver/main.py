"""
ESP32 Lego Power Functions Receiver Application

This is the main application for the wireless receiver device that drives motors.

Hardware Setup:
    - Motor 1: PWM=GPIO2, IN1=GPIO3, IN2=GPIO10
    - Motor 2: PWM=GPIO4, IN1=GPIO5, IN2=GPIO6
    - Pairing Button: GPIO9 (BOOT button, active low)
    - Status LED: GPIO8
    - ESP-NOW: WiFi interface

Button Behavior:
    - Held during power-up: Enter pairing mode
    - Not used during normal operation

Operation:
    - Listens for ESP-NOW control messages
    - Drives motors based on received speed/direction
    - Pairing modes:
      * Button held during power-up: Waits for pairing request (proactive)
      * During normal operation: Accepts pairing if not already paired (reactive)
      * When paired: Ignores pairing requests (security)
    - LED indicates status (on=receiving, fast blink=pairing, slow blink=idle)
    - Safety timeout stops motors if no messages received
"""

import sys
import time
from machine import Pin, PWM

# Add lib to path
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from button import Button
from motor_driver import MotorDriver, DualMotorDriver, MotorMode
from espnow_protocol import ESPNowProtocol, MessageType
from config_manager import ConfigManager


class ReceiverApp:
    """Main receiver application."""

    # Configuration keys
    CONFIG_PEER_MAC = 'peer_mac'

    # Safety timeout - stop motors if no messages received (ms)
    # Controller sends at 20Hz (50ms period), timeout at 2.5x = 125ms
    SAFETY_TIMEOUT_MS = 125

    # LED blink rate (Hz)
    PAIRING_BLINK_HZ = 4  # Fast blink during pairing
    IDLE_BLINK_HZ = 1     # Slow blink when idle

    # Pairing timeout
    PAIRING_TIMEOUT_SEC = 30

    def __init__(self):
        """Initialize receiver hardware and check for pairing mode."""
        print("\n" + "="*50)
        print("ESP32 Lego Power Functions Receiver")
        print("="*50)

        # Initialize configuration manager
        self.config = ConfigManager()

        # Initialize hardware
        print("\nInitializing hardware...")

        # Pairing button on GPIO9 (BOOT button, active low with pull-up)
        button_pin = Pin(9, Pin.IN, Pin.PULL_UP)
        self.button = Button(button_pin, active_low=True)

        # Motor 1: PWM=GPIO2, IN1=GPIO3, IN2=GPIO10
        pwm1 = PWM(Pin(2), freq=1000, duty=0)
        in1_1 = Pin(3, Pin.OUT)
        in2_1 = Pin(10, Pin.OUT)
        motor1 = MotorDriver(pwm1, in1_1, in2_1)

        # Motor 2: PWM=GPIO4, IN1=GPIO5, IN2=GPIO6
        pwm2 = PWM(Pin(4), freq=1000, duty=0)
        in1_2 = Pin(5, Pin.OUT)
        in2_2 = Pin(6, Pin.OUT)
        motor2 = MotorDriver(pwm2, in1_2, in2_2)

        # Dual motor controller
        self.motors = DualMotorDriver(motor1, motor2)

        # Status LED on GPIO8
        self.led = Pin(8, Pin.OUT)
        self.led.value(0)  # Start off

        # ESP-NOW protocol
        self.protocol = ESPNowProtocol('receiver')
        self.protocol.init()

        print("My MAC address:", self.protocol.get_mac_address_str())

        # Control state
        self.last_message_time = time.ticks_ms()
        self.active = False  # Receiving messages
        self.paired = False
        self.peer_mac = None
        self.pairing_mode = False

        # Check if button is held during power-up for pairing mode
        if self.button.is_pressed():
            print("\n*** BUTTON HELD - ENTERING PAIRING MODE ***")
            time.sleep_ms(100)  # Brief delay to confirm
            if self.button.is_pressed():  # Double-check
                self.pairing_mode = True
                self.enter_pairing_mode()
            else:
                print("Button released too quickly, continuing to normal mode")

        # Load paired peer from config if not in pairing mode
        if not self.pairing_mode:
            self.load_paired_peer()

        print("\nReceiver initialized")
        print("Paired:", "YES" if self.paired else "NO")
        if self.paired:
            print("Peer MAC:", ':'.join(['{:02X}'.format(b) for b in self.peer_mac]))

        # Start with motors stopped
        self.motors.stop_both(brake=True)

        print("\nReady to receive")

    def load_paired_peer(self):
        """Load paired peer MAC from configuration."""
        peer_mac_str = self.config.get(self.CONFIG_PEER_MAC)

        if peer_mac_str:
            try:
                # Convert string to bytes
                self.peer_mac = bytes.fromhex(peer_mac_str.replace(':', ''))
                self.protocol.add_peer(self.peer_mac)
                self.paired = True
                print("Loaded paired peer from config:", peer_mac_str)
            except Exception as e:
                print("Error loading peer MAC:", e)
                self.paired = False
        else:
            print("No paired peer in configuration")
            self.paired = False

    def enter_pairing_mode(self):
        """
        Enter pairing mode - wait for PAIR_REQUEST and respond.

        LED blinks fast while waiting for pairing.
        """
        print("\n" + "="*50)
        print("PAIRING MODE")
        print("="*50)
        print("\nWaiting for pairing request from controller...")
        print("Timeout: {} seconds\n".format(self.PAIRING_TIMEOUT_SEC))

        # Wait for PAIR_REQUEST with LED blinking
        start_time = time.time()
        led_state = False
        last_blink = time.time()
        blink_period = 1.0 / self.PAIRING_BLINK_HZ / 2  # Half period for toggle

        while time.time() - start_time < self.PAIRING_TIMEOUT_SEC:
            # Blink LED
            if time.time() - last_blink > blink_period:
                led_state = not led_state
                self.led.value(led_state)
                last_blink = time.time()

            # Check for PAIR_REQUEST
            msg = self.protocol.receive(timeout_ms=100)
            if msg and msg['type'] == MessageType.PAIR_REQUEST:
                # Got pairing request
                self.peer_mac = msg['sender_mac']
                peer_mac_str = ':'.join(['{:02X}'.format(b) for b in self.peer_mac])

                print("\n*** PAIRING REQUEST RECEIVED ***")
                print("From:", peer_mac_str)

                # Send acknowledgment
                self.protocol.send_pair_ack(self.peer_mac)
                print("Sent PAIR_ACK")

                # Add peer and save to config
                self.protocol.add_peer(self.peer_mac)
                self.config.set(self.CONFIG_PEER_MAC, peer_mac_str)
                self.paired = True

                print("Pairing saved to config")
                print("*** PAIRING COMPLETE ***\n")

                # LED on solid = paired
                self.led.value(1)
                time.sleep(2)  # Brief pause to show success
                return

        # Timeout
        print("\n*** PAIRING TIMEOUT ***")
        print("No controller paired")
        print("Device will continue in unpaired mode\n")
        self.led.value(0)  # LED off = not paired
        self.paired = False

    def handle_pairing_request(self, sender_mac):
        """
        Handle pairing request from controller.

        Args:
            sender_mac: MAC address of requesting controller
        """
        peer_mac_str = ':'.join(['{:02X}'.format(b) for b in sender_mac])

        print("\n*** PAIRING REQUEST ***")
        print("From:", peer_mac_str)

        # Send acknowledgment
        self.protocol.send_pair_ack(sender_mac)
        print("Sent PAIR_ACK")

        # Add as peer and save to config
        self.protocol.add_peer(sender_mac)
        self.peer_mac = sender_mac
        self.paired = True

        self.config.set(self.CONFIG_PEER_MAC, peer_mac_str)
        print("Pairing saved to config")
        print("*** PAIRING COMPLETE ***\n")

    def handle_control_message(self, msg):
        """
        Handle control message - drive motors.

        Args:
            msg: Decoded message dictionary with speed and direction
        """
        speed = msg['speed']
        direction = msg['direction']

        # Convert direction to MotorMode
        mode = MotorMode.FORWARD if direction == 0 else MotorMode.REVERSE

        # Drive both motors
        self.motors.drive_both(speed, mode)

        # Update state
        self.last_message_time = time.ticks_ms()
        self.active = True
        self.led.value(1)  # LED on = active

    def check_safety_timeout(self):
        """
        Check if we've exceeded safety timeout without messages.

        Stops motors if timeout exceeded.
        """
        if not self.active:
            return  # Already stopped

        elapsed = time.ticks_diff(time.ticks_ms(), self.last_message_time)

        if elapsed > self.SAFETY_TIMEOUT_MS:
            print("SAFETY TIMEOUT - stopping motors")
            self.motors.stop_both(brake=True)
            self.active = False
            # LED will blink in idle state

    def run(self):
        """
        Main receiver loop.

        Listens for messages and drives motors accordingly.
        Handles pairing requests only when not already paired (security).
        Implements safety timeout.
        """
        print("\n" + "="*50)
        print("RECEIVER RUNNING")
        print("="*50)
        print("\nListening for messages...")
        if self.paired:
            print("Paired mode - pairing requests will be ignored")
        else:
            print("Unpaired mode - will accept first pairing request")
        print("Safety timeout: {} ms".format(self.SAFETY_TIMEOUT_MS))
        print("Press Ctrl+C to stop\n")

        # LED blink state for idle
        led_blink_state = False
        last_blink_time = time.ticks_ms()
        blink_period_ms = int(1000 / self.IDLE_BLINK_HZ / 2)  # Half period for toggle

        try:
            while True:
                # Check for messages (non-blocking)
                msg = self.protocol.receive(timeout_ms=0)

                if msg:
                    if msg['type'] == MessageType.CONTROL:
                        # Control message - drive motors
                        self.handle_control_message(msg)

                        # Print status every 20 messages
                        if self.protocol.rx_total % 20 == 0:
                            print("Speed: {:3d}%  Direction: {}  Messages received: {}".format(
                                msg['speed'],
                                "FWD" if msg['direction'] == 0 else "REV",
                                self.protocol.rx_total
                            ))

                    elif msg['type'] == MessageType.PAIR_REQUEST:
                        # Pairing request - only accept if not already paired (security)
                        if not self.paired:
                            self.handle_pairing_request(msg['sender_mac'])
                        else:
                            # Already paired - ignore pairing requests
                            print("WARNING: Ignoring pairing request (already paired)")

                    elif msg['type'] == MessageType.PING:
                        # Ping request - respond with pong
                        if self.peer_mac != msg['sender_mac']:
                            self.protocol.add_peer(msg['sender_mac'])
                        self.protocol.send_pong()

                # Check safety timeout
                self.check_safety_timeout()

                # Update LED blinking when idle
                if not self.active:
                    if time.ticks_diff(time.ticks_ms(), last_blink_time) > blink_period_ms:
                        led_blink_state = not led_blink_state
                        self.led.value(led_blink_state)
                        last_blink_time = time.ticks_ms()

                # Small delay to avoid busy-waiting
                time.sleep_ms(1)

        except KeyboardInterrupt:
            print("\n\nReceiver stopped")
            print("Total messages received:", self.protocol.rx_total)

        finally:
            # Cleanup
            print("Shutting down...")
            self.motors.stop_both(brake=True)
            self.led.value(0)
            self.protocol.deinit()
            print("Motors stopped")
            print("Goodbye!")


# Create and run receiver
if __name__ == "__main__":
    receiver = ReceiverApp()
    receiver.run()
