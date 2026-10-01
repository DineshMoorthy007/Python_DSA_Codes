from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional

# RFC 7540 / RFC 8441 Setting Identifier
SETTINGS_ENABLE_CONNECT_PROTOCOL = 0x8  # Enabled if value == 1


class StreamState(IntEnum):
    IDLE = 0
    RESERVED = 1
    OPEN = 2
    HALF_CLOSED = 3
    CLOSED = 4


@dataclass
class HTTP2SettingsFrame:
    """Represents an HTTP/2 SETTINGS frame negotiation payload."""
    enable_connect_protocol: bool = False

    def encode(self) -> bytes:
        """Serializes settings into 6-byte identifier/value pairs."""
        payload = bytearray()
        if self.enable_connect_protocol:
            # Setting ID 0x0008 (2 bytes) = Value 0x00000001 (4 bytes)
            payload.extend(struct.pack("!HI", SETTINGS_ENABLE_CONNECT_PROTOCOL, 1))
        return bytes(payload)


@dataclass
class ExtendedConnectHeaders:
    """Pseudo-headers required for RFC 8441 Extended CONNECT WebSocket streams."""
    method: str = "CONNECT"
    protocol: str = "websocket"  # Required pseudo-header trigger
    scheme: str = "https"
    authority: str = "example.com"
    path: str = "/chat"
    sec_websocket_version: str = "13"
    sec_websocket_protocol: Optional[str] = None


class HTTP2WebSocketStream:
    """Manages an individual multiplexed WebSocket stream within an HTTP/2 connection."""

    def __init__(self, stream_id: int):
        self.stream_id = stream_id
        self.state = StreamState.IDLE
        self.is_websocket_stream = False
        self.subprotocol: Optional[str] = None

    def open_extended_connect(self, headers: ExtendedConnectHeaders) -> bool:
        """Initiates Extended CONNECT stream creation."""
        if self.state != StreamState.IDLE:
            print(f"  [STREAM {self.stream_id} ERROR] Stream is not in IDLE state.")
            return False

        if headers.method != "CONNECT" or headers.protocol != "websocket":
            print(f"  [STREAM {self.stream_id} ERROR] Invalid Extended CONNECT pseudo-headers.")
            return False

        self.is_websocket_stream = True
        self.state = StreamState.OPEN
        self.subprotocol = headers.sec_websocket_protocol
        print(f"  [STREAM {self.stream_id} OPENED] Initiated HTTP/2 Extended CONNECT WebSocket stream")
        return True

    def receive_response(self, status_code: int) -> bool:
        """Processes server HTTP/2 HEADERS frame response (200 OK confirms stream)."""
        if self.state != StreamState.OPEN:
            return False

        if status_code == 200:
            print(f"  [STREAM {self.stream_id} SUCCESS] Server returned 200 OK. WebSocket stream active over HTTP/2!")
            return True
        else:
            print(f"  [STREAM {self.stream_id} REJECTED] Server returned {status_code}.")
            self.state = StreamState.CLOSED
            return False


class HTTP2WebSocketNegotiator:
    """Negotiates RFC 8441 connection-level capabilities and manages multiplexed streams."""

    def __init__(self):
        self.peer_connect_protocol_enabled = False
        self.active_streams: Dict[int, HTTP2WebSocketStream] = {}

    def receive_settings(self, settings: HTTP2SettingsFrame) -> None:
        """Processes incoming SETTINGS frame from peer."""
        self.peer_connect_protocol_enabled = settings.enable_connect_protocol
        status = "ENABLED" if settings.enable_connect_protocol else "DISABLED"
        print(f"  [HTTP/2 SETTINGS] SETTINGS_ENABLE_CONNECT_PROTOCOL is {status}")

    def create_websocket_stream(self, stream_id: int, headers: ExtendedConnectHeaders) -> Optional[HTTP2WebSocketStream]:
        """Creates a multiplexed WebSocket stream if connection capabilities permit."""
        if not self.peer_connect_protocol_enabled:
            print("  [NEGOTIATION FAILED] Peer has not enabled SETTINGS_ENABLE_CONNECT_PROTOCOL.")
            return None

        stream = HTTP2WebSocketStream(stream_id=stream_id)
        if stream.open_extended_connect(headers):
            self.active_streams[stream_id] = stream
            return stream
        return None


# --- Extended CONNECT Simulation Script ---

if __name__ == "__main__":
    import struct

    print("--- Initializing HTTP/2 RFC 8441 Extended CONNECT WebSocket Negotiator ---\n")

    negotiator = HTTP2WebSocketNegotiator()

    print("[STEP 1: HTTP/2 Connection Handshake & Settings Exchange]")
    # Server advertises support for Extended CONNECT via SETTINGS frame
    server_settings = HTTP2SettingsFrame(enable_connect_protocol=True)
    negotiator.receive_settings(server_settings)
    print("-" * 65)

    print("\n[STEP 2: Constructing RFC 8441 Extended CONNECT Request Headers]")
    connect_headers = ExtendedConnectHeaders(
        authority="realtime.example.com",
        path="/v1/feed",
        sec_websocket_protocol="json-v1"
    )
    print(f"  :method   = {connect_headers.method}")
    print(f"  :protocol = {connect_headers.protocol}")
    print(f"  :scheme   = {connect_headers.scheme}")
    print(f"  :path     = {connect_headers.path}")
    print("-" * 65)

    print("\n[STEP 3: Opening Multiplexed WebSocket Stream #3]")
    stream = negotiator.create_websocket_stream(stream_id=3, headers=connect_headers)

    print("\n[STEP 4: Server Processing & Stream Activation]")
    if stream:
        # Server accepts Extended CONNECT with 200 OK (NOT 101 Switching Protocols!)
        stream.receive_response(status_code=200)

    print("-" * 65)
    print("[SUCCESS] Established multiplexed WebSocket stream over HTTP/2 without connection takeover!")

# Output :
# --- Initializing HTTP/2 RFC 8441 Extended CONNECT WebSocket Negotiator ---

# [STEP 1: HTTP/2 Connection Handshake & Settings Exchange]
#   [HTTP/2 SETTINGS] SETTINGS_ENABLE_CONNECT_PROTOCOL is ENABLED
# -----------------------------------------------------------------

# [STEP 2: Constructing RFC 8441 Extended CONNECT Request Headers]
#   :method   = CONNECT
#   :protocol = websocket
#   :scheme   = https
#   :path     = /v1/feed
# -----------------------------------------------------------------

# [STEP 3: Opening Multiplexed WebSocket Stream #3]
#   [STREAM 3 OPENED] Initiated HTTP/2 Extended CONNECT WebSocket stream

# [STEP 4: Server Processing & Stream Activation]
#   [STREAM 3 SUCCESS] Server returned 200 OK. WebSocket stream active over HTTP/2!
# -----------------------------------------------------------------
# [SUCCESS] Established multiplexed WebSocket stream over HTTP/2 without connection takeover!
