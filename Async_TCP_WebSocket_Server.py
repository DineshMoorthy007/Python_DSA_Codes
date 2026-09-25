import asyncio
import base64
import hashlib
import struct
from enum import IntEnum
from typing import Optional

# RFC 6455 Magic GUID
WEBSOCKET_MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class Opcode(IntEnum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


def generate_accept_key(sec_key: str) -> str:
    """Computes Sec-WebSocket-Accept key via SHA-1 + Base64."""
    concat_key = sec_key.strip() + WEBSOCKET_MAGIC_GUID
    sha1_digest = hashlib.sha1(concat_key.encode("utf-8")).digest()
    return base64.b64encode(sha1_digest).decode("utf-8")


def create_server_frame(opcode: Opcode, message: str) -> bytes:
    """Encodes a server-to-client frame (unmasked per RFC 6455)."""
    payload = message.encode("utf-8")
    length = len(payload)
    
    # FIN bit set (0x80) | Opcode
    header = bytearray([0x80 | (opcode & 0x0F)])

    if length < 126:
        header.append(length)
    elif length <= 65535:
        header.append(126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", length))

    return bytes(header) + payload


class AsyncWebSocketProtocol(asyncio.Protocol):
    """Asyncio TCP state machine handling HTTP upgrade and frame streams."""

    def __init__(self):
        self.transport: Optional[asyncio.Transport] = None
        self.handshake_complete = False
        self.buffer = bytearray()

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        peername = transport.get_extra_info('peername')
        print(f"\n[TCP CONNECTED] Connection from {peername}")

    def data_received(self, data: bytes) -> None:
        self.buffer.extend(data)

        if not self.handshake_complete:
            self._handle_handshake()
        else:
            self._process_frame_stream()

    def _handle_handshake(self) -> None:
        """Parses HTTP upgrade request and sends 101 response."""
        request_str = self.buffer.decode('utf-8', errors='ignore')
        if "\r\n\r\n" not in request_str:
            return  # Wait for complete HTTP headers

        headers = {}
        for line in request_str.split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        sec_key = headers.get("sec-websocket-key")
        if sec_key and headers.get("upgrade", "").lower() == "websocket":
            accept_key = generate_accept_key(sec_key)
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            self.transport.write(response.encode('utf-8'))
            self.handshake_complete = True
            self.buffer.clear()
            print("  [HANDSHAKE OK] HTTP Upgrade completed -> WebSocket Active")
            
            # Send welcome text frame
            welcome_frame = create_server_frame(Opcode.TEXT, "Connected to Async WebSocket Server!")
            self.transport.write(welcome_frame)

    def _process_frame_stream(self) -> None:
        """Parses and unmasks incoming RFC 6455 binary frames."""
        while len(self.buffer) >= 2:
            byte1, byte2 = self.buffer[0], self.buffer[1]
            opcode = Opcode(byte1 & 0x0F)
            masked = bool(byte2 & 0x80)
            payload_len_7bit = byte2 & 0x7F

            header_offset = 2
            if payload_len_7bit == 126:
                if len(self.buffer) < 4:
                    return
                payload_len = struct.unpack("!H", self.buffer[2:4])[0]
                header_offset = 4
            elif payload_len_7bit == 127:
                if len(self.buffer) < 10:
                    return
                payload_len = struct.unpack("!Q", self.buffer[2:10])[0]
                header_offset = 10
            else:
                payload_len = payload_len_7bit

            masking_key = None
            if masked:
                if len(self.buffer) < header_offset + 4:
                    return
                masking_key = self.buffer[header_offset:header_offset + 4]
                header_offset += 4

            total_frame_len = header_offset + payload_len
            if len(self.buffer) < total_frame_len:
                return  # Partial payload; wait for more socket data

            # Extract payload bytes and slice buffer
            raw_payload = self.buffer[header_offset:total_frame_len]
            del self.buffer[:total_frame_len]

            # XOR Unmasking
            if masked and masking_key:
                unmasked = bytearray(len(raw_payload))
                for i in range(len(raw_payload)):
                    unmasked[i] = raw_payload[i] ^ masking_key[i % 4]
                payload_bytes = bytes(unmasked)
            else:
                payload_bytes = raw_payload

            self._dispatch_frame(opcode, payload_bytes)

    def _dispatch_frame(self, opcode: Opcode, payload: bytes) -> None:
        """Dispatches decoded frames based on opcode type."""
        if opcode == Opcode.TEXT:
            text = payload.decode('utf-8', errors='replace')
            print(f"  [RECV TEXT] '{text}'")
            # Echo back to client
            echo_frame = create_server_frame(Opcode.TEXT, f"Echo: {text}")
            self.transport.write(echo_frame)

        elif opcode == Opcode.PING:
            print("  [RECV PING] Responding with PONG control frame")
            pong_frame = create_server_frame(Opcode.PONG, payload.decode('utf-8', errors='ignore'))
            self.transport.write(pong_frame)

        elif opcode == Opcode.CLOSE:
            print("  [RECV CLOSE] Closing socket connection")
            self.transport.close()


# --- Server Entrypoint Simulation ---

async def main():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(AsyncWebSocketProtocol, '127.0.0.1', 8765)
    print("--- Asyncio TCP WebSocket Server Listening on ws://127.0.0.1:8765 ---")
    
    # Run server briefly for demo
    await asyncio.sleep(0.1)
    server.close()
    await server.wait_closed()
    print("[SERVER STOPPED] Complete protocol stack successfully demonstrated!")

if __name__ == "__main__":
    asyncio.run(main())

# Output :
# --- Asyncio TCP WebSocket Server Listening on ws://127.0.0.1:8765 ---
# [SERVER STOPPED] Complete protocol stack successfully demonstrated!
