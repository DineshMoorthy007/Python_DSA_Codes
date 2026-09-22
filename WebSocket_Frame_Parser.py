import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple


class Opcode(IntEnum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


@dataclass
class Frame:
    fin: bool
    opcode: Opcode
    masked: bool
    payload_length: int
    masking_key: Optional[bytes]
    payload_data: bytes

    def unmasked_payload(self) -> bytes:
        """Applies 4-byte XOR unmasking transformation required for client-to-server frames.
        
        RFC 6455 Section 5.3:
          transformed-octet-i = original-octet-i XOR masking-key-item-(i MOD 4)
        """
        if not self.masked or not self.masking_key:
            return self.payload_data

        unmasked = bytearray(len(self.payload_data))
        for i in range(len(self.payload_data)):
            unmasked[i] = self.payload_data[i] ^ self.masking_key[i % 4]
        return bytes(unmasked)


class WebSocketFrameParser:
    """Wire-protocol state machine parser for RFC 6455 WebSocket binary frames."""

    @staticmethod
    def parse_frame(buffer: bytes) -> Tuple[Optional[Frame], bytes]:
        """Parses a single frame from raw byte buffer.
        
        Returns (Frame, remaining_buffer_bytes).
        """
        if len(buffer) < 2:
            return None, buffer  # Need at least 2 header bytes

        byte1, byte2 = buffer[0], buffer[1]

        # Byte 1: FIN (1 bit), RSV1-3 (3 bits), Opcode (4 bits)
        fin = bool(byte1 & 0x80)
        opcode_raw = byte1 & 0x0F
        try:
            opcode = Opcode(opcode_raw)
        except ValueError:
            raise ValueError(f"Invalid WebSocket Opcode: 0x{opcode_raw:X}")

        # Byte 2: MASK (1 bit), Payload Len (7 bits)
        masked = bool(byte2 & 0x80)
        payload_len_7bit = byte2 & 0x7F

        header_offset = 2

        # Extended payload length handling
        if payload_len_7bit == 126:
            if len(buffer) < header_offset + 2:
                return None, buffer  # Incomplete frame header
            payload_length = struct.unpack("!H", buffer[header_offset:header_offset + 2])[0]
            header_offset += 2
        elif payload_len_7bit == 127:
            if len(buffer) < header_offset + 8:
                return None, buffer  # Incomplete frame header
            payload_length = struct.unpack("!Q", buffer[header_offset:header_offset + 8])[0]
            header_offset += 8
        else:
            payload_length = payload_len_7bit

        # Extract 4-byte Masking Key if present
        masking_key = None
        if masked:
            if len(buffer) < header_offset + 4:
                return None, buffer  # Incomplete masking key
            masking_key = buffer[header_offset:header_offset + 4]
            header_offset += 4

        # Check total frame size availability in buffer
        total_frame_size = header_offset + payload_length
        if len(buffer) < total_frame_size:
            return None, buffer  # Incomplete payload body; wait for more socket data

        # Slice payload data and remaining unparsed stream buffer
        payload_data = buffer[header_offset:total_frame_size]
        remaining_buffer = buffer[total_frame_size:]

        frame = Frame(
            fin=fin,
            opcode=opcode,
            masked=masked,
            payload_length=payload_length,
            masking_key=masking_key,
            payload_data=payload_data,
        )

        return frame, remaining_buffer


@dataclass
class WebSocketBuilder:
    """Utility to build wire-format WebSocket frames for testing."""

    @staticmethod
    def create_frame(opcode: Opcode, message: str, masked: bool = True) -> bytes:
        payload = message.encode("utf-8")
        fin_opcode_byte = 0x80 | (opcode & 0x0F)  # FIN = 1
        
        mask_bit = 0x80 if masked else 0x00
        length = len(payload)

        buffer = bytearray()
        buffer.append(fin_opcode_byte)

        if length < 126:
            buffer.append(mask_bit | length)
        elif length <= 65535:
            buffer.append(mask_bit | 126)
            buffer.extend(struct.pack("!H", length))
        else:
            buffer.append(mask_bit | 127)
            buffer.extend(struct.pack("!Q", length))

        if masked:
            masking_key = bytes([0x12, 0x34, 0x56, 0x78])  # Static test mask
            buffer.extend(masking_key)
            masked_payload = bytearray(length)
            for i in range(length):
                masked_payload[i] = payload[i] ^ masking_key[i % 4]
            buffer.extend(masked_payload)
        else:
            buffer.extend(payload)

        return bytes(buffer)


# --- Wire Frame Parser Simulation ---

if __name__ == "__main__":
    print("--- Initializing WebSocket RFC 6455 Frame Parser & Unmasking Engine ---\n")

    # Construct raw wire bytes representing client frames
    text_frame_raw = WebSocketBuilder.create_frame(
        Opcode.TEXT, message="Hello WebSocket World!", masked=True
    )
    ping_frame_raw = WebSocketBuilder.create_frame(
        Opcode.PING, message="keepalive-ping", masked=True
    )

    # Stream multiple frames into a single binary TCP socket buffer stream
    tcp_socket_stream = text_frame_raw + ping_frame_raw

    print(f"Total Raw Byte Buffer Received from Socket: {len(tcp_socket_stream)} bytes")
    print(f"Raw Wire Bytes (Hex): {tcp_socket_stream.hex()}")
    print("-" * 65)

    # Stream parsing loop
    buffer = tcp_socket_stream
    frame_count = 0

    while buffer:
        frame, buffer = WebSocketFrameParser.parse_frame(buffer)
        if not frame:
            print("  Buffer exhausted or partial frame received. Stopping parser loop.")
            break

        frame_count += 1
        decoded_payload = frame.unmasked_payload().decode("utf-8", errors="replace")

        print(f"\n[PARSED FRAME #{frame_count}]")
        print(f"  FIN Bit       : {frame.fin}")
        print(f"  Opcode        : {frame.opcode.name} (0x{frame.opcode.value:X})")
        print(f"  Masked        : {frame.masked}")
        print(f"  Payload Length: {frame.payload_length} bytes")
        if frame.masking_key:
            print(f"  Mask Key (Hex): {frame.masking_key.hex()}")
        print(f"  Decoded Output: '{decoded_payload}'")

    print("-" * 65)
    print("[SUCCESS] Fully decoded wire frames, unmasked byte payloads, and handled control opcodes!")

# Output :
# --- Initializing WebSocket RFC 6455 Frame Parser & Unmasking Engine ---

# Total Raw Byte Buffer Received from Socket: 48 bytes
# Raw Wire Bytes (Hex): 8196123456785a513a147d14011d7067391b79512258455b24147615898e123456787951330873583f0e771926117c53
# -----------------------------------------------------------------

# [PARSED FRAME #1]
#   FIN Bit       : True
#   Opcode        : TEXT (0x1)
#   Masked        : True
#   Payload Length: 22 bytes
#   Mask Key (Hex): 12345678
#   Decoded Output: 'Hello WebSocket World!'

# [PARSED FRAME #2]
#   FIN Bit       : True
#   Opcode        : PING (0x9)
#   Masked        : True
#   Payload Length: 14 bytes
#   Mask Key (Hex): 12345678
#   Decoded Output: 'keepalive-ping'
# -----------------------------------------------------------------
# [SUCCESS] Fully decoded wire frames, unmasked byte payloads, and handled control opcodes!
