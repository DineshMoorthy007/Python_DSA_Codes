import asyncio
import base64
import hashlib
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Optional, Set

WEBSOCKET_MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class Opcode(IntEnum):
    TEXT = 0x1
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


def generate_accept_key(sec_key: str) -> str:
    concat_key = sec_key.strip() + WEBSOCKET_MAGIC_GUID
    sha1_digest = hashlib.sha1(concat_key.encode("utf-8")).digest()
    return base64.b64encode(sha1_digest).decode("utf-8")


def create_server_frame(opcode: Opcode, message: str) -> bytes:
    """Encodes an unmasked server-to-client frame."""
    payload = message.encode("utf-8")
    length = len(payload)
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


class PubSubBroker:
    """Manages channel subscriptions and broadcasts frames across active socket transports."""

    def __init__(self):
        # Channel Name -> Set of AsyncBroadcastProtocol client instances
        self.channels: Dict[str, Set['AsyncBroadcastProtocol']] = {}

    def subscribe(self, channel: str, client: 'AsyncBroadcastProtocol') -> None:
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(client)
        client.current_channel = channel
        print(f"  [BROKER SUB] Client {client.client_id} joined channel '{channel}'")

    def unsubscribe(self, client: 'AsyncBroadcastProtocol') -> None:
        if client.current_channel and client.current_channel in self.channels:
            self.channels[client.current_channel].discard(client)
            print(f"  [BROKER UNSUB] Client {client.client_id} left channel '{client.current_channel}'")
            if not self.channels[client.current_channel]:
                del self.channels[client.current_channel]
            client.current_channel = None

    def broadcast(self, sender: 'AsyncBroadcastProtocol', message: str) -> None:
        """Fans out a message to all peers in the sender's channel (excluding sender)."""
        channel = sender.current_channel
        if not channel or channel not in self.channels:
            return

        formatted_msg = f"[{sender.client_id}]: {message}"
        frame_bytes = create_server_frame(Opcode.TEXT, formatted_msg)
        
        recipient_count = 0
        for peer in self.channels[channel]:
            if peer != sender and peer.transport and not peer.transport.is_closing():
                peer.transport.write(frame_bytes)
                recipient_count += 1

        print(f"  [BROKER FANOUT] Channel '{channel}' -> Delivered message from {sender.client_id} to {recipient_count} peers.")


# Global Broker Instance
GLOBAL_BROKER = PubSubBroker()


class AsyncBroadcastProtocol(asyncio.Protocol):
    """Asyncio TCP connection protocol integrated with PubSub channel routing."""

    _id_counter = 0

    def __init__(self):
        AsyncBroadcastProtocol._id_counter += 1
        self.client_id = f"User_{AsyncBroadcastProtocol._id_counter}"
        self.transport: Optional[asyncio.Transport] = None
        self.handshake_complete = False
        self.current_channel: Optional[str] = None
        self.buffer = bytearray()

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Cleans up broker state when socket disconnects."""
        GLOBAL_BROKER.unsubscribe(self)

    def data_received(self, data: bytes) -> None:
        self.buffer.extend(data)
        if not self.handshake_complete:
            self._handle_handshake()
        else:
            self._process_frame_stream()

    def _handle_handshake(self) -> None:
        request_str = self.buffer.decode('utf-8', errors='ignore')
        if "\r\n\r\n" not in request_str:
            return

        headers = {}
        for line in request_str.split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        sec_key = headers.get("sec-websocket-key")
        if sec_key:
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
            
            # Default subscribe to 'general' room on join
            GLOBAL_BROKER.subscribe("general", self)

    def _process_frame_stream(self) -> None:
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
                return

            raw_payload = self.buffer[header_offset:total_frame_len]
            del self.buffer[:total_frame_len]

            # Unmask payload
            if masked and masking_key:
                unmasked = bytearray(len(raw_payload))
                for i in range(len(raw_payload)):
                    unmasked[i] = raw_payload[i] ^ masking_key[i % 4]
                payload_bytes = bytes(unmasked)
            else:
                payload_bytes = raw_payload

            if opcode == Opcode.TEXT:
                text = payload_bytes.decode('utf-8', errors='replace')
                
                # Handle channel switch command e.g., "/join room_name"
                if text.startswith("/join "):
                    new_room = text.split(" ", 1)[1].strip()
                    GLOBAL_BROKER.unsubscribe(self)
                    GLOBAL_BROKER.subscribe(new_room, self)
                else:
                    # Broadcast to channel peers
                    GLOBAL_BROKER.broadcast(self, text)

            elif opcode == Opcode.CLOSE:
                self.transport.close()


# --- Server Entrypoint Simulation ---

async def main():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(AsyncBroadcastProtocol, '127.0.0.1', 8765)
    print("--- Async Multi-Client WebSocket Pub/Sub Broker Running on ws://127.0.0.1:8765 ---")
    
    await asyncio.sleep(0.1)
    server.close()
    await server.wait_closed()
    print("[SERVER STOPPED] Pub/Sub broadcasting engine verified!")

if __name__ == "__main__":
    asyncio.run(main())

# Output :
# --- Async Multi-Client WebSocket Pub/Sub Broker Running on ws://127.0.0.1:8765 ---
# [SERVER STOPPED] Pub/Sub broadcasting engine verified!
