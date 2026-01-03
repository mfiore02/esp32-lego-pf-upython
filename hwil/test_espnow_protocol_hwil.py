"""
Hardware-in-Loop Test for ESP-NOW Protocol

This script tests ESP-NOW communication between two ESP32 devices.

To run:
    1. Flash to BOTH devices:
       mpremote connect COM3 fs cp hwil/test_espnow_protocol_hwil.py :main.py
       mpremote connect COM3 fs cp lib/espnow_protocol.py :lib/espnow_protocol.py

    2. Choose mode on each device via REPL:
       Device 1 (Controller): test_sender()
       Device 2 (Receiver): test_receiver()

    3. Follow on-screen instructions

Expected behavior:
    - Devices discover each other
    - Messages sent/received successfully
    - Low latency (<10ms typical)

Hardware setup:
    - Two ESP32-C3 devices
    - No wiring needed (WiFi communication)
    - Both devices powered on
"""

import sys
import time

# Add lib to path if needed
if '/lib' not in sys.path:
    sys.path.insert(0, '/lib')

from espnow_protocol import ESPNowProtocol, MessageType


def test_sender():
    """
    Sender test - continuously sends control messages.

    Run this on the CONTROLLER device.
    """

    print("\n" + "="*50)
    print("ESP-NOW Sender Test (Controller Mode)")
    print("="*50)

    protocol = ESPNowProtocol('controller')
    protocol.init()

    print("\nMy MAC address:", protocol.get_mac_address_str())
    print("\nEnter receiver MAC address (format: AA:BB:CC:DD:EE:FF)")
    print("or press Enter to broadcast pairing request")

    # In actual use, you'd get this from config or manual entry
    # For testing, we'll use broadcast pairing
    receiver_mac = input("Receiver MAC (or Enter): ").strip()

    if receiver_mac:
        protocol.add_peer(receiver_mac)
        print("Peer added:", receiver_mac)
    else:
        print("\nSending pairing request...")
        protocol.send_pair_request()
        print("Waiting for receiver to respond...")
        print("(Make sure receiver is running test_receiver())")
        #time.sleep(2)

        # Listen for pair acknowledgment
        start_time = time.time()
        paired = False

        while time.time() - start_time < 10:
            msg = protocol.receive(timeout_ms=100)
            if msg and msg['type'] == MessageType.PAIR_ACK:
                receiver_mac = msg['sender_mac']
                protocol.add_peer(receiver_mac)
                print("\nPaired with:", ':'.join(['{:02X}'.format(b) for b in receiver_mac]))
                paired = True
                break

        if not paired:
            print("\nPairing failed - no response")
            print("Make sure receiver is running and try again")
            return

    print("\nStarting transmission...")
    print("Sending control messages (speed cycling 0-100)")
    print("Press Ctrl+C to stop\n")

    speed = 0
    direction = 0
    msg_count = 0

    try:
        while True:
            # Get current sequence before sending
            current_seq = protocol.sequence

            # Send control message
            protocol.send_control(speed, direction)
            msg_count += 1

            # Print each message sent
            print("SENT seq={} speed={} dir={}".format(
                current_seq, speed, "FWD" if direction == 0 else "REV"
            ))

            # Update speed (cycle 0-100)
            speed = (speed + 5) % 105

            # Toggle direction occasionally
            if speed == 0:
                direction = 1 - direction

            time.sleep_ms(500)  # 2Hz update rate (slower for debugging)

    except KeyboardInterrupt:
        print("\n\nTransmission stopped")
        print("Total messages sent:", msg_count)


def test_receiver():
    """
    Receiver test - listens for and displays control messages.

    Run this on the RECEIVER device.
    """

    print("\n" + "="*50)
    print("ESP-NOW Receiver Test (Receiver Mode)")
    print("="*50)

    protocol = ESPNowProtocol('receiver')
    protocol.init()

    print("\nMy MAC address:", protocol.get_mac_address_str())
    print("Share this with the controller!\n")
    print("Listening for messages...")
    print("(Controller should run test_sender())")
    print("Press Ctrl+C to stop\n")

    msg_count = 0
    last_sequence = -1
    missed_messages = 0

    try:
        while True:
            msg = protocol.receive(timeout_ms=100)

            if msg:
                msg_count += 1

                # Check for missed messages (sequence gaps)
                if last_sequence >= 0:
                    expected_seq = (last_sequence + 1) % 256
                    if msg['sequence'] != expected_seq:
                        gap = (msg['sequence'] - expected_seq) % 256
                        missed_messages += gap
                        print("!!! MISSED {} messages (expected seq={}, got seq={})".format(
                            gap, expected_seq, msg['sequence']
                        ))

                last_sequence = msg['sequence']

                # Handle message types
                if msg['type'] == MessageType.CONTROL:
                    print("RECV seq={} speed={} dir={} (total={} missed={})".format(
                        msg['sequence'],
                        msg['speed'],
                        "FWD" if msg['direction'] == 0 else "REV",
                        msg_count,
                        missed_messages
                    ))

                elif msg['type'] == MessageType.PAIR_REQUEST:
                    print("\n[PAIR] Received pairing request from:",
                          ':'.join(['{:02X}'.format(b) for b in msg['sender_mac']]))

                    # Send acknowledgment
                    protocol.send_pair_ack(msg['sender_mac'])
                    print("[PAIR] Sent acknowledgment")

                    # Add as peer
                    protocol.add_peer(msg['sender_mac'])
                    print("[PAIR] Pairing complete!\n")

                elif msg['type'] == MessageType.PING:
                    # Respond to ping
                    protocol.add_peer(msg['sender_mac'])
                    protocol.send_pong()

    except KeyboardInterrupt:
        print("\n\nReception stopped")
        print("Total messages received:", msg_count)
        print("Missed messages:", missed_messages)
        if msg_count > 0:
            loss_rate = (missed_messages / (msg_count + missed_messages)) * 100
            print("Message loss rate: {:.2f}%".format(loss_rate))


def test_ping():
    """
    Ping test - measures round-trip latency.

    Requires second device running test_receiver() or test_pong_responder().
    """

    print("\n" + "="*50)
    print("ESP-NOW Ping Test")
    print("="*50)

    protocol = ESPNowProtocol('controller')
    protocol.init()

    print("\nMy MAC address:", protocol.get_mac_address_str())
    print("Enter peer MAC address:")
    peer_mac = input("Peer MAC: ").strip()

    if not peer_mac:
        print("No peer specified")
        return

    protocol.add_peer(peer_mac)
    print("Peer added\n")
    print("Sending ping requests...")
    print("Press Ctrl+C to stop\n")

    latencies = []

    try:
        for i in range(10):
            # Send ping
            start_time = time.ticks_us()
            protocol.send_ping()

            # Wait for pong
            timeout_time = time.ticks_add(start_time, 100000)  # 100ms timeout

            while time.ticks_diff(time.ticks_us(), start_time) < 100000:
                msg = protocol.receive(timeout_ms=10)
                if msg and msg['type'] == MessageType.PONG:
                    # Got response
                    latency_us = time.ticks_diff(time.ticks_us(), start_time)
                    latency_ms = latency_us / 1000.0
                    latencies.append(latency_ms)
                    print("Ping {} reply: {:.2f} ms".format(i + 1, latency_ms))
                    break
            else:
                print("Ping {} timeout".format(i + 1))

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nPing test stopped")

    if latencies:
        print("\n--- Ping Statistics ---")
        print("Sent: 10, Received: {}".format(len(latencies)))
        print("Min: {:.2f} ms".format(min(latencies)))
        print("Max: {:.2f} ms".format(max(latencies)))
        print("Avg: {:.2f} ms".format(sum(latencies) / len(latencies)))


def test_pong_responder():
    """
    Pong responder - responds to ping requests.

    Run this on second device for ping testing.
    """

    print("\n" + "="*50)
    print("ESP-NOW Pong Responder")
    print("="*50)

    protocol = ESPNowProtocol('receiver')
    protocol.init()

    print("\nMy MAC address:", protocol.get_mac_address_str())
    print("Waiting for ping requests...")
    print("Press Ctrl+C to stop\n")

    pong_count = 0

    try:
        while True:
            msg = protocol.receive(timeout_ms=100)

            if msg and msg['type'] == MessageType.PING:
                # Add sender as peer if not already
                if protocol.peer_mac != msg['sender_mac']:
                    protocol.add_peer(msg['sender_mac'])

                # Send pong response
                protocol.send_pong()
                pong_count += 1
                print("Pong sent ({})".format(pong_count))

    except KeyboardInterrupt:
        print("\nResponder stopped")
        print("Total pongs sent:", pong_count)


# Print menu
print("\n" + "="*50)
print("ESP-NOW Protocol HWIL Tests")
print("="*50)
print("\nAvailable tests:")
print("  test_sender() - Send control messages (run on controller)")
print("  test_receiver() - Receive messages (run on receiver)")
print("  test_ping() - Measure latency (requires receiver)")
print("  test_pong_responder() - Respond to pings")
print("\nExample: Run test_receiver() on device 1,")
print("         then test_sender() on device 2")
print("\nCall a test function from REPL to begin")
