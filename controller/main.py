"""
ESP32 Lego Power Functions Controller Application

This is the main application for the wireless controller device.

Hardware Setup:
    - Button: GPIO10 (active low, internal pull-up)
    - Potentiometer: GPIO1 (ADC)
    - Status LED: GPIO8
    - ESP-NOW: WiFi interface

Button Behavior:
    - Held during power-up: Enter pairing mode
    - Press during operation: Toggle direction (forward/reverse)

Operation:
    - Potentiometer controls speed (0-100%)
    - Button toggles direction
    - Sends control messages at 20Hz to paired receiver
    - LED indicates status (on=paired, blink=pairing, off=error)
"""

import sys
import time
from machine import Pin, ADC

# Add lib to path
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from button import Button
from potentiometer import Potentiometer
from espnow_protocol import ESPNowProtocol, MessageType
from config_manager import ConfigManager


class ControllerApp:
    """Main controller application."""

    # Configuration keys
    CONFIG_PEER_MAC = 'peer_mac'

    # Control loop rate (Hz)
    CONTROL_RATE_HZ = 20
    CONTROL_PERIOD_MS = int(1000 / CONTROL_RATE_HZ)

    # Pairing timeout
    PAIRING_TIMEOUT_SEC = 30

    def __init__(self):
        """Initialize controller hardware and check for pairing mode."""
        print("\n" + "="*50)
        print("ESP32 Lego Power Functions Controller")
        print("="*50)

        # Initialize configuration manager
        self.config = ConfigManager(ConfigManager.DEVICE_CONTROLLER)

        # Initialize hardware
        print("\nInitializing hardware...")

        # Button on GPIO10 (active low with pull-up)
        button_pin = Pin(10, Pin.IN, Pin.PULL_UP)
        self.button = Button(button_pin, active_low=True)

        # Potentiometer on GPIO1 (ADC)
        adc = ADC(Pin(1))
        adc.atten(ADC.ATTN_11DB)  # Full 0-3.3V range
        self.pot = Potentiometer(adc)

        # Status LED on GPIO8
        self.led = Pin(8, Pin.OUT)
        self.led.value(0)  # Start off

        # ESP-NOW protocol
        self.protocol = ESPNowProtocol('controller')
        self.protocol.init()

        print("My MAC address:", self.protocol.get_mac_address_str())

        # Control state
        self.speed = 0
        self.direction = 0  # 0=forward, 1=reverse
        self.paired = False
        self.peer_mac = None

        # Check if button is held during power-up for pairing mode
        # Wait for debounce period, then call update() to read debounced state
        time.sleep_ms(60)  # Wait longer than 50ms debounce time
        self.button.update()  # Now debounced state will be set if button is still pressed

        if self.button.is_pressed():
            print("\n*** BUTTON HELD - ENTERING PAIRING MODE ***")
            time.sleep_ms(100)  # Brief delay to confirm
            self.button.update()
            if self.button.is_pressed():  # Double-check
                self.enter_pairing_mode()
            else:
                print("Button released too quickly, continuing to normal mode")

        # Load paired peer from config if not in pairing mode
        if not self.paired:
            self.load_paired_peer()

        print("\nController initialized")
        print("Paired:", "YES" if self.paired else "NO")
        if self.paired:
            print("Peer MAC:", ':'.join(['{:02X}'.format(b) for b in self.peer_mac]))
            self.led.value(1)  # LED on = paired
        else:
            print("\nWARNING: No paired receiver!")
            print("Hold button during power-up to enter pairing mode")
            self.led.value(0)  # LED off = not paired

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
        Enter pairing mode - send broadcast PAIR_REQUEST and wait for PAIR_ACK.

        LED blinks while waiting for pairing.
        """
        print("\n" + "="*50)
        print("PAIRING MODE")
        print("="*50)
        print("\nSending pairing request...")
        print("Make sure receiver is powered on and ready")
        print("Timeout: {} seconds\n".format(self.PAIRING_TIMEOUT_SEC))

        # Send pairing request
        self.protocol.send_pair_request()

        # Wait for PAIR_ACK with LED blinking
        start_time = time.time()
        led_state = False
        last_blink = time.time()

        while time.time() - start_time < self.PAIRING_TIMEOUT_SEC:
            # Blink LED at 2Hz
            if time.time() - last_blink > 0.25:
                led_state = not led_state
                self.led.value(led_state)
                last_blink = time.time()

            # Check for PAIR_ACK
            msg = self.protocol.receive(timeout_ms=100)
            if msg and msg['type'] == MessageType.PAIR_ACK:
                # Got pairing acknowledgment
                self.peer_mac = msg['sender_mac']
                peer_mac_str = ':'.join(['{:02X}'.format(b) for b in self.peer_mac])

                print("\n*** PAIRING SUCCESS ***")
                print("Paired with:", peer_mac_str)

                # Add peer and save to config
                self.protocol.add_peer(self.peer_mac)
                self.config.set(self.CONFIG_PEER_MAC, peer_mac_str)
                self.config.save()  # Persist to filesystem
                self.paired = True

                print("Pairing saved to config")

                # LED on solid = paired
                self.led.value(1)

                print("\nPairing complete!")
                time.sleep(2)  # Brief pause to show success
                return

            # Resend pairing request every 2 seconds
            if int(time.time() - start_time) % 2 == 0:
                self.protocol.send_pair_request()
                time.sleep_ms(100)  # Avoid spamming

        # Timeout
        print("\n*** PAIRING TIMEOUT ***")
        print("No receiver responded")
        print("Please try again\n")
        self.led.value(0)  # LED off = failed
        self.paired = False

    def run(self):
        """
        Main control loop.

        Reads potentiometer for speed, button for direction toggle,
        and sends control messages at 20Hz.
        """
        if not self.paired:
            print("\nCannot run - not paired with receiver")
            print("Hold button during power-up to enter pairing mode")
            return

        print("\n" + "="*50)
        print("CONTROLLER RUNNING")
        print("="*50)
        print("\nControls:")
        print("  Potentiometer: Speed (0-100%)")
        print("  Button: Toggle direction")
        print("\nSending control messages at {}Hz".format(self.CONTROL_RATE_HZ))
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                loop_start = time.ticks_ms()

                # Update button state
                self.button.update()

                # Check for button press (direction toggle)
                if self.button.was_pressed():
                    self.direction = 1 - self.direction
                    print("Direction toggled:", "FORWARD" if self.direction == 0 else "REVERSE")

                # Read speed from potentiometer
                self.speed = self.pot.read()

                # Send control message
                self.protocol.send_control(self.speed, self.direction)

                # Print status every 10 messages
                if self.protocol.tx_total % 10 == 0:
                    print("Speed: {:3d}%  Direction: {}  Messages sent: {}".format(
                        self.speed,
                        "FWD" if self.direction == 0 else "REV",
                        self.protocol.tx_total
                    ))

                # Maintain control rate
                elapsed = time.ticks_diff(time.ticks_ms(), loop_start)
                sleep_time = self.CONTROL_PERIOD_MS - elapsed

                if sleep_time > 0:
                    time.sleep_ms(sleep_time)
                else:
                    # Loop took longer than period - log warning
                    if self.protocol.tx_total % 20 == 0:  # Don't spam
                        print("WARNING: Control loop overrun by {} ms".format(-sleep_time))

        except KeyboardInterrupt:
            print("\n\nController stopped")
            print("Total messages sent:", self.protocol.tx_total)

        finally:
            # Cleanup
            print("Shutting down...")
            self.led.value(0)
            self.protocol.deinit()
            print("Goodbye!")


# Create and run controller
if __name__ == "__main__":
    controller = ControllerApp()
    controller.run()
