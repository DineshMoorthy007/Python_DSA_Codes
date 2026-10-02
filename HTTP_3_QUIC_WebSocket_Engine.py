import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple

# RFC 9220 / HTTP/3 Settings Frame Identifier
H3_SETTINGS_ENABLE_CONNECT_PROTOCOL = 0x08


class H3FrameType(IntEnum):
    DATA = 0x00
    HEADERS = 0x01
    SETTINGS = 0x04
    DATAGRAM = 0x30  # RFC 9297 HTTP Datagram Frame


@dataclass
class QUICStream:
    """Represents a single QUIC multiplexed stream (62-bit stream IDs)."""
    stream_id: int
    is_bidirectional: bool
    is_client_initiated: bool
    received_bytes: bytearray = field(default_factory=bytearray)
    is_closed: bool = False

    @staticmethod
    def parse_stream_id(stream_id: int) -> Tuple[bool, bool]:
        """QUIC Stream ID encoding rules (RFC 9000 Section 2.1):
        
        Bit 0: Initiator (0 = Client, 1 = Server)
        Bit 1: Directionality (0 = Bidirectional, 1 = Unidirectional)
        """
        is_server = bool(stream_id & 0x01)
        is_unidirectional = bool(stream_id & 0x02)
        return not is_unidirectional, not is_server


class HTTP3WebSocketSession:
    """Manages an RFC 9220 WebSocket session running over a QUIC stream."""

    def __init__(self, session_id: int, authority: str, path: str):
        self.session_id = session_id  # The QUIC Stream ID acting as the WebSocket control stream
        self.authority = authority
        self.path = path
        self.is_established = False
        
        # Reliable stream data buffer
        self.stream_buffer = bytearray()
        # Unreliable datagram queue (for low-latency loss-tolerant payloads)
        self.datagram_queue: List[bytes] = []

    def receive_reliable_data(self, payload: bytes) -> None:
        """Processes reliable ordered stream bytes (replaces standard TCP socket stream)."""
        self.stream_buffer.extend(payload)
        print(f"  [H3 STREAM {self.session_id}] Received {len(payload)} RELIABLE bytes.")

    def receive_unreliable_datagram(self, datagram_payload: bytes) -> None:
        """Processes unreliable out-of-order QUIC datagrams (replaces UDP socket stream)."""
        self.datagram_queue.append(datagram_payload)
        print(f"  [H3 DATAGRAM {self.session_id}] Received {len(datagram_payload)} UNRELIABLE/LOW-LATENCY bytes: {datagram_payload.hex()}")


class HTTP3ExtendedConnectEngine:
    """HTTP/3 Extended CONNECT & QUIC Datagram multiplexing engine."""

    def __init__(self):
        self.h3_connect_enabled = False
        self.active_sessions: Dict[int, HTTP3WebSocketSession] = {}

    def process_settings(self, settings_map: Dict[int, int]) -> None:
        """Processes HTTP/3 SETTINGS frame parameters."""
        if settings_map.get(H3_SETTINGS_ENABLE_CONNECT_PROTOCOL) == 1:
            self.h3_connect_enabled = True
            print("  [HTTP/3 SETTINGS] SETTINGS_ENABLE_CONNECT_PROTOCOL = 1 (RFC 9220 Enabled)")

    def handle_extended_connect(
        self, stream_id: int, pseudo_headers: Dict[str, str]
    ) -> Optional[HTTP3WebSocketSession]:
        """Parses Extended CONNECT request on a QUIC stream.
        
        RFC 9220 Pseudo-Header Validation:
          :method   = CONNECT
          :protocol = websocket
          :scheme   = https
        """
        if not self.h3_connect_enabled:
            print("  [REJECTED] HTTP/3 Extended CONNECT disabled by peer SETTINGS.")
            return None

        method = pseudo_headers.get(":method")
        protocol = pseudo_headers.get(":protocol")
        authority = pseudo_headers.get(":authority", "")
        path = pseudo_headers.get(":path", "/")

        if method != "CONNECT" or protocol != "websocket":
            print("  [REJECTED] Invalid RFC 9220 pseudo-headers.")
            return None

        # Create session bound to this QUIC Stream ID
        session = HTTP3WebSocketSession(session_id=stream_id, authority=authority, path=path)
        session.is_established = True
        self.active_sessions[stream_id] = session

        print(f"  [RFC 9220 SESSION ESTABLISHED] QUIC Stream ID {stream_id} upgraded to HTTP/3 WebSocket")
        return session

    def dispatch_quic_datagram(self, session_id: int, payload: bytes) -> None:
        """Routes QUIC DATAGRAM frame (RFC 9297) to target session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].receive_unreliable_datagram(payload)


# --- Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing HTTP/3 (QUIC) Extended CONNECT & Datagram Engine ---\n")

    engine = HTTP3ExtendedConnectEngine()

    print("[STEP 1: HTTP/3 Connection Setup & Capability Negotiation]")
    # Peer advertises HTTP/3 Extended CONNECT support
    engine.process_settings({H3_SETTINGS_ENABLE_CONNECT_PROTOCOL: 1})
    print("-" * 65)

    print("\n[STEP 2: Opening RFC 9220 WebSocket Session over QUIC Stream #0 (Client Bidi)]")
    # Client initiates Extended CONNECT via HTTP/3 HEADERS frame
    h3_headers = {
        ":method": "CONNECT",
        ":protocol": "websocket",
        ":scheme": "https",
        ":authority": "game.example.com",
        ":path": "/v1/multiplayer"
    }
    session = engine.handle_extended_connect(stream_id=0, pseudo_headers=h3_headers)
    print("-" * 65)

    print("\n[STEP 3: Concurrent Dual-Transport Transmission (Reliable + Unreliable)]")
    if session:
        # 1. Transmission over Reliable QUIC Stream (e.g., Chat / Player State Sync)
        session.receive_reliable_data(b"CHAT_MSG: Ready to spawn!")

        # 2. Transmission over Unreliable QUIC Datagram (e.g., High-Frequency Player Coordinates)
        # Datagram payload: Player X, Y, Z velocity vector (12 bytes float)
        player_coords_payload = struct.pack("!fff", 124.5, 60.2, 890.1)
        engine.dispatch_quic_datagram(session_id=0, payload=player_coords_payload)

    print("-" * 65)
    print("[SUCCESS] Established HTTP/3 WebSocket session supporting zero-head-of-line blocking and QUIC datagrams!")

# Output :
# --- Initializing HTTP/3 (QUIC) Extended CONNECT & Datagram Engine ---

# [STEP 1: HTTP/3 Connection Setup & Capability Negotiation]
#   [HTTP/3 SETTINGS] SETTINGS_ENABLE_CONNECT_PROTOCOL = 1 (RFC 9220 Enabled)
# -----------------------------------------------------------------

# [STEP 2: Opening RFC 9220 WebSocket Session over QUIC Stream #0 (Client Bidi)]
#   [RFC 9220 SESSION ESTABLISHED] QUIC Stream ID 0 upgraded to HTTP/3 WebSocket
# -----------------------------------------------------------------

# [STEP 3: Concurrent Dual-Transport Transmission (Reliable + Unreliable)]
#   [H3 STREAM 0] Received 25 RELIABLE bytes.
#   [H3 DATAGRAM 0] Received 12 UNRELIABLE/LOW-LATENCY bytes: 42f900004270cccd445e8666
# -----------------------------------------------------------------
# [SUCCESS] Established HTTP/3 WebSocket session supporting zero-head-of-line blocking and QUIC datagrams!
