"""
Unit tests for ESP-NOW Protocol module

Run with: python -m pytest tests/test_espnow_protocol.py -v
"""

import sys
import struct
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


# Mock network and espnow modules
class MockWLAN:
    """Mock WiFi WLAN class."""

    def __init__(self, mode):
        self.mode = mode
        self._active = False
        self._mac = b'\xAA\xBB\xCC\xDD\xEE\xFF'

    def active(self, state=None):
        if state is not None:
            self._active = state
        return self._active

    def config(self, param=None, **kwargs):
        if param == 'mac':
            return self._mac
        return None


class MockESPNow:
    """Mock ESP-NOW class."""

    def __init__(self):
        self._active = False
        self.peers = []
        self.sent_messages = []
        self.receive_queue = []

    def active(self, state=None):
        if state is not None:
            self._active = state
        return self._active

    def add_peer(self, mac):
        if mac not in self.peers:
            self.peers.append(mac)

    def del_peer(self, mac):
        if mac in self.peers:
            self.peers.remove(mac)

    def get_peers(self):
        """Return list of peers in format [(mac, channel, ifidx, encrypt), ...]"""
        # Return simplified format - just need MAC in first position
        return [(peer, 0, 0, False) for peer in self.peers]

    def send(self, mac, msg):
        self.sent_messages.append((mac, msg))

    def recv(self, timeout_ms=0):
        if self.receive_queue:
            return self.receive_queue.pop(0)
        return (None, None)


# Inject mocks into sys.modules
sys.modules['network'] = type('module', (), {
    'WLAN': MockWLAN,
    'STA_IF': 0
})()

sys.modules['espnow'] = type('module', (), {
    'ESPNow': MockESPNow
})()


class TestESPNowProtocol:
    """Test ESP-NOW protocol message handling."""

    def test_message_encoding_control(self):
        """Test control message encoding."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        # Send control message
        protocol.send_control(speed=75, direction=1)

        # Check sent message
        assert len(protocol.e.sent_messages) == 1
        mac, msg = protocol.e.sent_messages[0]

        assert mac == b'\x11\x22\x33\x44\x55\x66'
        assert len(msg) == 4

        # Decode and verify
        msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)
        assert msg_type == MessageType.CONTROL
        assert sequence == 0  # First message
        assert speed == 75
        assert direction == 1

    def test_message_decoding_control(self):
        """Test control message decoding."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('receiver')
        protocol.init()

        # Create control message
        msg = struct.pack('!BBBB', MessageType.CONTROL, 5, 80, 0)

        # Queue message for receive
        sender_mac = b'\xAA\xBB\xCC\xDD\xEE\xFF'
        protocol.e.receive_queue.append((sender_mac, msg))

        # Receive and decode
        decoded = protocol.receive()

        assert decoded is not None
        assert decoded['type'] == MessageType.CONTROL
        assert decoded['sequence'] == 5
        assert decoded['speed'] == 80
        assert decoded['direction'] == 0
        assert decoded['sender_mac'] == sender_mac

    def test_sequence_counter(self):
        """Test sequence number increments."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        # Send multiple messages
        for i in range(5):
            protocol.send_control(speed=50, direction=0)

        # Check sequences
        for i, (mac, msg) in enumerate(protocol.e.sent_messages):
            msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)
            assert sequence == i

    def test_ping_message(self):
        """Test ping message."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        protocol.send_ping()

        mac, msg = protocol.e.sent_messages[0]
        msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)

        assert msg_type == MessageType.PING
        assert speed == 0
        assert direction == 0

    def test_pong_message(self):
        """Test pong message."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('receiver')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        protocol.send_pong()

        mac, msg = protocol.e.sent_messages[0]
        msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)

        assert msg_type == MessageType.PONG

    def test_pair_request_broadcast(self):
        """Test pairing request broadcasts."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('controller')
        protocol.init()

        protocol.send_pair_request()

        # Should broadcast (to FF:FF:FF:FF:FF:FF)
        mac, msg = protocol.e.sent_messages[0]
        assert mac == b'\xff\xff\xff\xff\xff\xff'

        msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)
        assert msg_type == MessageType.PAIR_REQUEST

    def test_pair_ack(self):
        """Test pairing acknowledgment."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('receiver')
        protocol.init()

        peer_mac = b'\x11\x22\x33\x44\x55\x66'
        protocol.send_pair_ack(peer_mac)

        mac, msg = protocol.e.sent_messages[0]
        assert mac == peer_mac

        msg_type, sequence, speed, direction = struct.unpack('!BBBB', msg)
        assert msg_type == MessageType.PAIR_ACK

    def test_mac_address_format(self):
        """Test MAC address formatting."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()

        mac_str = protocol.get_mac_address_str()
        assert mac_str == 'AA:BB:CC:DD:EE:FF'

    def test_add_remove_peer(self):
        """Test adding and removing peers."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()

        peer_mac = b'\x11\x22\x33\x44\x55\x66'

        # Add peer
        protocol.add_peer(peer_mac)
        assert peer_mac in protocol.e.peers
        assert protocol.peer_mac == peer_mac

        # Remove peer
        protocol.remove_peer()
        assert peer_mac not in protocol.e.peers
        assert protocol.peer_mac is None

    def test_add_peer_string_format(self):
        """Test adding peer with string MAC address."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()

        # Add peer with string format
        protocol.add_peer('11:22:33:44:55:66')

        expected_mac = b'\x11\x22\x33\x44\x55\x66'
        assert expected_mac in protocol.e.peers

    def test_no_peer_send_fails(self):
        """Test sending without peer configured."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()

        # Should fail gracefully
        result = protocol.send_control(50, 0)
        assert result is False

    def test_invalid_message_size(self):
        """Test handling of invalid message size."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('receiver')
        protocol.init()

        # Queue invalid message (wrong size)
        protocol.e.receive_queue.append((b'\xAA\xBB\xCC\xDD\xEE\xFF', b'\x01\x02'))

        decoded = protocol.receive()
        assert decoded is None  # Should reject invalid message

    def test_sequence_wraparound(self):
        """Test sequence number wraparound at 255."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        # Set sequence near wraparound
        protocol.sequence = 254

        protocol.send_control(50, 0)
        protocol.send_control(50, 0)
        protocol.send_control(50, 0)

        # Check sequences wrapped correctly
        sequences = []
        for mac, msg in protocol.e.sent_messages:
            msg_type, seq, speed, direction = struct.unpack('!BBBB', msg)
            sequences.append(seq)

        assert sequences == [254, 255, 0]  # Should wrap to 0

    def test_device_type_initialization(self):
        """Test initialization with different device types."""
        from espnow_protocol import ESPNowProtocol

        controller = ESPNowProtocol('controller')
        assert controller.device_type == 'controller'

        receiver = ESPNowProtocol('receiver')
        assert receiver.device_type == 'receiver'

    def test_counters_initialization(self):
        """Test tx_total and rx_total initialize to 0."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        assert protocol.tx_total == 0
        assert protocol.rx_total == 0
        assert protocol.sequence == 0

    def test_tx_total_increments(self):
        """Test tx_total increments on successful send."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        # Send multiple messages
        protocol.send_control(50, 0)
        assert protocol.tx_total == 1

        protocol.send_control(75, 1)
        assert protocol.tx_total == 2

        protocol.send_ping()
        assert protocol.tx_total == 3

        protocol.send_pong()
        assert protocol.tx_total == 4

    def test_rx_total_increments(self):
        """Test rx_total increments on successful receive."""
        from espnow_protocol import ESPNowProtocol, MessageType

        protocol = ESPNowProtocol('receiver')
        protocol.init()

        # Queue multiple messages
        msg1 = struct.pack('!BBBB', MessageType.CONTROL, 0, 50, 0)
        msg2 = struct.pack('!BBBB', MessageType.CONTROL, 1, 75, 1)
        msg3 = struct.pack('!BBBB', MessageType.PING, 2, 0, 0)

        sender_mac = b'\xAA\xBB\xCC\xDD\xEE\xFF'
        protocol.e.receive_queue.append((sender_mac, msg1))
        protocol.e.receive_queue.append((sender_mac, msg2))
        protocol.e.receive_queue.append((sender_mac, msg3))

        # Receive messages
        protocol.receive()
        assert protocol.rx_total == 1

        protocol.receive()
        assert protocol.rx_total == 2

        protocol.receive()
        assert protocol.rx_total == 3

    def test_tx_total_not_incremented_on_failed_send(self):
        """Test tx_total doesn't increment when send fails."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()
        # No peer configured - send should fail

        result = protocol.send_control(50, 0)
        assert result is False
        assert protocol.tx_total == 0
        assert protocol.sequence == 0  # Sequence shouldn't increment either

    def test_sequence_and_tx_total_independent(self):
        """Test sequence wraps at 256 while tx_total continues unbounded."""
        from espnow_protocol import ESPNowProtocol

        protocol = ESPNowProtocol('controller')
        protocol.init()
        protocol.add_peer(b'\x11\x22\x33\x44\x55\x66')

        # Set sequence near wraparound
        protocol.sequence = 255

        protocol.send_control(50, 0)
        assert protocol.sequence == 0  # Wrapped to 0
        assert protocol.tx_total == 1  # But total keeps counting

        protocol.send_control(50, 0)
        assert protocol.sequence == 1
        assert protocol.tx_total == 2

        # Verify we can go well beyond 256 messages
        protocol.sequence = 255
        protocol.tx_total = 500

        protocol.send_control(50, 0)
        assert protocol.sequence == 0  # Still wraps
        assert protocol.tx_total == 501  # But total continues


print("ESP-NOW protocol tests created successfully")
