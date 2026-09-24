import base64
import hashlib
from dataclasses import dataclass
from typing import Dict

# RFC 6455 Section 1.3 - Globally Unique Identifier (UUID/GUID)
WEBSOCKET_MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def generate_accept_key(sec_websocket_key: str) -> str:
    """Computes the Sec-WebSocket-Accept header value per RFC 6455.
    
    1. Concatenate Sec-WebSocket-Key with Magic GUID string.
    2. Compute SHA-1 digest of concatenated string.
    3. Base64-encode the SHA-1 digest bytes.
    """
    concat_key = sec_websocket_key.strip() + WEBSOCKET_MAGIC_GUID
    sha1_digest = hashlib.sha1(concat_key.encode("utf-8")).digest()
    return base64.b64encode(sha1_digest).decode("utf-8")


@dataclass
class HandshakeResult:
    is_valid: bool
    status_code: int
    raw_response: str
    error_message: str = ""


class WebSocketHandshakeHandler:
    """Parses HTTP upgrade requests and generates RFC 6455 compliant handshake responses."""

    @staticmethod
    def process_upgrade_request(raw_http_request: str) -> HandshakeResult:
        """Parses raw HTTP request headers and validates WebSocket Upgrade requirements."""
        lines = raw_http_request.strip().split("\r\n")
        if not lines:
            return HandshakeResult(False, 400, "", "Empty request buffer")

        # Parse Request Line (e.g., "GET /chat HTTP/1.1")
        request_line = lines[0].split()
        if len(request_line) < 3 or request_line[0] != "GET":
            return HandshakeResult(False, 405, "", "WebSocket handshake must be a GET request")

        # Parse HTTP Headers into a case-insensitive dictionary
        headers: Dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        # Validate mandatory RFC 6455 headers
        if headers.get("upgrade", "").lower() != "websocket":
            return HandshakeResult(False, 400, "", "Missing or invalid 'Upgrade: websocket' header")

        if "connection" not in headers or "upgrade" not in headers["connection"].lower():
            return HandshakeResult(False, 400, "", "Missing or invalid 'Connection: Upgrade' header")

        sec_key = headers.get("sec-websocket-key")
        if not sec_key:
            return HandshakeResult(False, 400, "", "Missing 'Sec-WebSocket-Key' header")

        # Validate base64 length of client key (16 raw bytes encoded = 24 chars with padding)
        try:
            decoded_key = base64.b64decode(sec_key)
            if len(decoded_key) != 16:
                return HandshakeResult(False, 400, "", "Sec-WebSocket-Key must decode to exactly 16 bytes")
        except Exception:
            return HandshakeResult(False, 400, "", "Malformed base64 Sec-WebSocket-Key")

        # Compute Sec-WebSocket-Accept token
        accept_key = generate_accept_key(sec_key)

        # Construct HTTP/1.1 101 Switching Protocols response
        response_headers = [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Accept: {accept_key}",
        ]

        # Preserve subprotocol negotiation if client requested one
        if "sec-websocket-protocol" in headers:
            subprotocol = headers["sec-websocket-protocol"].split(",")[0].strip()
            response_headers.append(f"Sec-WebSocket-Protocol: {subprotocol}")

        response_bytes = "\r\n".join(response_headers) + "\r\n\r\n"
        return HandshakeResult(True, 101, response_bytes)


# --- Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing WebSocket HTTP Upgrade Handshake Negotiator ---\n")

    # Simulate a client HTTP Upgrade Request payload
    client_request = (
        "GET /chat HTTP/1.1\r\n"
        "Host: server.example.com\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Origin: http://example.com\r\n"
        "Sec-WebSocket-Protocol: chat, superchat\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )

    print("[1. RAW CLIENT HTTP UPGRADE REQUEST]")
    print(client_request.strip())
    print("-" * 65)

    # Process handshake
    result = WebSocketHandshakeHandler.process_upgrade_request(client_request)

    print("[2. SERVER HANDSHAKE PROCESSING RESULT]")
    print(f"  Handshake Success : {result.is_valid}")
    print(f"  HTTP Status Code  : {result.status_code}")
    print("-" * 65)

    print("[3. GENERATED HTTP/1.1 101 SWITCHING PROTOCOLS RESPONSE]")
    print(result.raw_response.strip())
    print("-" * 65)

    # Verification check against RFC 6455 Section 1.3 example key
    # Key: "dGhlIHNhbXBsZSBub25jZQ==" -> Expected Accept: "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    expected_accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    computed_accept = generate_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
    
    assert computed_accept == expected_accept
    print("[VERIFICATION] RFC 6455 Standard Sample Match!")
    print("  Client Key   : dGhlIHNhbXBsZSBub25jZQ==")
    print(f"  Accept Key   : {computed_accept}")
    print("[SUCCESS] HTTP socket connection successfully upgraded to binary WebSocket framing protocol!")

# Output :
# --- Initializing WebSocket HTTP Upgrade Handshake Negotiator ---

# [1. RAW CLIENT HTTP UPGRADE REQUEST]
# GET /chat HTTP/1.1
# Host: server.example.com
# Upgrade: websocket
# Connection: Upgrade
# Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
# Origin: http://example.com
# Sec-WebSocket-Protocol: chat, superchat
# Sec-WebSocket-Version: 13
# -----------------------------------------------------------------
# [2. SERVER HANDSHAKE PROCESSING RESULT]
#   Handshake Success : True
#   HTTP Status Code  : 101
# -----------------------------------------------------------------
# [3. GENERATED HTTP/1.1 101 SWITCHING PROTOCOLS RESPONSE]
# HTTP/1.1 101 Switching Protocols
# Upgrade: websocket
# Connection: Upgrade
# Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
# Sec-WebSocket-Protocol: chat
# -----------------------------------------------------------------
# [VERIFICATION] RFC 6455 Standard Sample Match!
#   Client Key   : dGhlIHNhbXBsZSBub25jZQ==
#   Accept Key   : s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
# [SUCCESS] HTTP socket connection successfully upgraded to binary WebSocket framing protocol!
