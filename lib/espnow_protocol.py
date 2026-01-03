"""
ESP-NOW Protocol Module

Provides ESP-NOW communication with message protocol for controller-receiver link.
Handles pairing, message encoding/decoding, and reliable transmission.

Example usage - Receiver:
    from espnow_protocol import ESPNowProtocol, MessageType

    protocol = ESPNowProtocol(device_type='receiver')
    protocol.init()

    # Wait for messages
    while True:
        msg = protocol.receive()
        if msg:
            if msg['type'] == MessageType.CONTROL:
                speed = msg['speed']
                direction = msg['direction']
                print("Speed:", speed, "Direction:", direction)

Example usage - Controller:
    from espnow_protocol import ESPNowProtocol, MessageType

    protocol = ESPNowProtocol(device_type='controller')
    protocol.init()
    protocol.add_peer(receiver_mac)

    # Send control messages
    protocol.send_control(speed=75, direction=1)
"""

import network
import espnow
import struct
import time


class MessageType:
    """Message type constants."""

    CONTROL = 0x01      # Speed/direction control message
    PING = 0x02         # Ping request
    PONG = 0x03         # Ping response
    PAIR_REQUEST = 0x10 # Pairing request
    PAIR_ACK = 0x11     # Pairing acknowledgment


class ESPNowProtocol:
    """ESP-NOW protocol handler with message encoding/decoding."""

    # Message format: type(1) + sequence(1) + speed(1) + direction(1) = 4 bytes
    MSG_FORMAT = '!BBBB'
    MSG_SIZE = 4

    def __init__(self, device_type='controller'):
        """
        Initialize ESP-NOW protocol.

        Args:
            device_type: 'controller' or 'receiver'
        """
        self.device_type = device_type
        self.e = None
        self.sta = None
        self.sequence = 0  # Message sequence counter

        # Paired peer MAC address
        self.peer_mac = None

    def init(self):
        """Initialize ESP-NOW and WiFi interface."""
        # Initialize WiFi in station mode
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)

        # Set WiFi channel (optional, can improve reliability)
        # self.sta.config(channel=1)

        # Initialize ESP-NOW
        self.e = espnow.ESPNow()
        self.e.active(True)

        print("ESP-NOW initialized")
        print("MAC address:", self.get_mac_address())

    def get_mac_address(self):
        """
        Get device MAC address as bytes.

        Returns:
            MAC address as 6-byte bytearray
        """
        if self.sta:
            return self.sta.config('mac')
        return None

    def get_mac_address_str(self):
        """
        Get device MAC address as formatted string.

        Returns:
            MAC address as string (e.g., "AA:BB:CC:DD:EE:FF")
        """
        mac = self.get_mac_address()
        if mac:
            return ':'.join(['{:02X}'.format(b) for b in mac])
        return None

    def add_peer(self, peer_mac):
        """
        Add peer device for communication.

        Args:
            peer_mac: Peer MAC address as bytes (6 bytes)
        """
        try:
            # Convert to bytes if string
            if isinstance(peer_mac, str):
                peer_mac = bytes.fromhex(peer_mac.replace(':', ''))

            self.e.add_peer(peer_mac)
            self.peer_mac = peer_mac
            print("Peer added:", ':'.join(['{:02X}'.format(b) for b in peer_mac]))
        except Exception as e:
            print("Error adding peer:", e)

    def remove_peer(self, peer_mac=None):
        """
        Remove peer device.

        Args:
            peer_mac: Peer MAC to remove, or None to remove current peer
        """
        if peer_mac is None:
            peer_mac = self.peer_mac

        if peer_mac:
            try:
                self.e.del_peer(peer_mac)
                if peer_mac == self.peer_mac:
                    self.peer_mac = None
                print("Peer removed")
            except Exception as e:
                print("Error removing peer:", e)

    def send_control(self, speed, direction):
        """
        Send control message with speed and direction.

        Args:
            speed: Speed value (0-100)
            direction: Direction (0=forward, 1=reverse)

        Returns:
            True if sent successfully, False otherwise
        """
        msg = struct.pack(
            self.MSG_FORMAT,
            MessageType.CONTROL,
            self.sequence & 0xFF,
            int(speed) & 0xFF,
            int(direction) & 0xFF
        )

        self.sequence += 1
        return self._send(msg)

    def send_ping(self):
        """
        Send ping message.

        Returns:
            True if sent successfully, False otherwise
        """
        msg = struct.pack(
            self.MSG_FORMAT,
            MessageType.PING,
            self.sequence & 0xFF,
            0,
            0
        )

        self.sequence += 1
        return self._send(msg)

    def send_pong(self):
        """
        Send pong response.

        Returns:
            True if sent successfully, False otherwise
        """
        msg = struct.pack(
            self.MSG_FORMAT,
            MessageType.PONG,
            self.sequence & 0xFF,
            0,
            0
        )

        self.sequence += 1
        return self._send(msg)

    def send_pair_request(self):
        """
        Send pairing request.

        Returns:
            True if sent successfully, False otherwise
        """
        msg = struct.pack(
            self.MSG_FORMAT,
            MessageType.PAIR_REQUEST,
            self.sequence & 0xFF,
            0,
            0
        )

        self.sequence += 1
        return self._send(msg, broadcast=True)

    def send_pair_ack(self, peer_mac):
        """
        Send pairing acknowledgment.

        Args:
            peer_mac: MAC address of device to pair with

        Returns:
            True if sent successfully, False otherwise
        """
        # Temporarily add peer for acknowledgment
        original_peer = self.peer_mac
        self.add_peer(peer_mac)

        msg = struct.pack(
            self.MSG_FORMAT,
            MessageType.PAIR_ACK,
            self.sequence & 0xFF,
            0,
            0
        )

        self.sequence += 1
        success = self._send(msg)

        # Restore original peer if different
        if original_peer != peer_mac:
            self.peer_mac = original_peer

        return success

    def receive(self, timeout_ms=0):
        """
        Receive and decode message.

        Args:
            timeout_ms: Timeout in milliseconds (0 = non-blocking)

        Returns:
            Dictionary with message data, or None if no message
            {
                'type': MessageType constant,
                'sequence': Sequence number,
                'speed': Speed value (for CONTROL messages),
                'direction': Direction value (for CONTROL messages),
                'sender_mac': Sender MAC address as bytes
            }
        """
        # Check for message
        host, msg = self.e.recv(timeout_ms)

        if msg is None:
            return None

        # Decode message
        try:
            if len(msg) != self.MSG_SIZE:
                print("Invalid message size:", len(msg))
                return None

            msg_type, sequence, speed, direction = struct.unpack(self.MSG_FORMAT, msg)

            return {
                'type': msg_type,
                'sequence': sequence,
                'speed': speed,
                'direction': direction,
                'sender_mac': host
            }

        except Exception as e:
            print("Error decoding message:", e)
            return None

    def _send(self, msg, broadcast=False):
        """
        Send raw message via ESP-NOW.

        Args:
            msg: Message bytes to send
            broadcast: True to broadcast, False to send to peer

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if broadcast:
                # Send to broadcast address
                self.e.send(b'\xff\xff\xff\xff\xff\xff', msg)
            elif self.peer_mac:
                # Send to paired peer
                self.e.send(self.peer_mac, msg)
            else:
                print("No peer configured")
                return False

            return True

        except Exception as e:
            print("Error sending message:", e)
            return False

    def deinit(self):
        """Deinitialize ESP-NOW and WiFi."""
        if self.e:
            self.e.active(False)
        if self.sta:
            self.sta.active(False)
