import os
import struct
import zlib
from typing import Iterator

class WALEntry:
    """Represents a discrete mutation record formatted for binary serialization."""
    
    # Binary Payload Envelope: LSN (Q = uint64), Command (10s = 10 chars), Data Length (I = uint32)
    HEADER_FORMAT = "!Q10sI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, lsn: int, command: str, payload: str):
        self.lsn = lsn
        self.command = command.strip().ljust(10)  # Fixed-width 10-char string
        self.payload = payload.encode('utf-8')

    def serialize(self) -> bytes:
        """Serializes entry with a 32-bit CRC32 checksum appended at the end."""
        header = struct.pack(self.HEADER_FORMAT, self.lsn, self.command.encode('utf-8'), len(self.payload))
        record_body = header + self.payload
        checksum = zlib.crc32(record_body) & 0xFFFFFFFF
        return record_body + struct.pack("!I", checksum)

    @classmethod
    def deserialize_from_file(cls, file_obj) -> 'WALEntry | None':
        """Parses and validates a WAL record from a raw file stream."""
        header_bytes = file_obj.read(cls.HEADER_SIZE)
        if not header_bytes or len(header_bytes) < cls.HEADER_SIZE:
            return None  # End of log

        lsn, command_raw, payload_len = struct.unpack(cls.HEADER_FORMAT, header_bytes)
        payload = file_obj.read(payload_len)
        checksum_bytes = file_obj.read(4)

        if len(checksum_bytes) < 4:
            raise ValueError("Corrupted Log: Incomplete record checksum frame.")

        stored_checksum = struct.unpack("!I", checksum_bytes)[0]
        calculated_checksum = zlib.crc32(header_bytes + payload) & 0xFFFFFFFF

        if stored_checksum != calculated_checksum:
            raise ValueError(f"Corrupted Log: Checksum mismatch at LSN {lsn}!")

        command = command_raw.decode('utf-8').strip()
        return cls(lsn, command, payload.decode('utf-8'))


class WriteAheadLog:
    """Manages appending durable transactions and recovering state after a crash."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._next_lsn = 1
        
        # If file exists, scan to determine the highest active LSN
        if os.path.exists(filepath):
            for entry in self.replay():
                self._next_lsn = entry.lsn + 1

    def append(self, command: str, payload: str) -> int:
        """Appends a mutation to the log file and forces an explicit disk sync (fsync)."""
        entry = WALEntry(self._next_lsn, command, payload)
        serialized_bytes = entry.serialize()

        # Open in append-binary mode
        with open(self.filepath, "a+b") as f:
            f.write(serialized_bytes)
            f.flush()
            os.fsync(f.fileno())  # Force OS buffer cache commit to physical storage

        assigned_lsn = self._next_lsn
        self._next_lsn += 1
        return assigned_lsn

    def replay(self) -> Iterator[WALEntry]:
        """Reads through the WAL sequentially from start to end for crash recovery."""
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath, "rb") as f:
            while True:
                entry = WALEntry.deserialize_from_file(f)
                if entry is None:
                    break
                yield entry


if __name__ == "__main__":
    log_filename = "transactions.wal"
    
    # Cleanup previous run logs for clean execution
    if os.path.exists(log_filename):
        os.remove(log_filename)

    print("--- Phase 1: Operating Normal Transactions ---")
    wal = WriteAheadLog(log_filename)
    
    lsn1 = wal.append("SET_VAL", "user:101=Alice")
    lsn2 = wal.append("SET_VAL", "user:102=Bob")
    lsn3 = wal.append("DEL_VAL", "user:101")
    
    print(f"  [WAL] Appended LSNs {lsn1}, {lsn2}, {lsn3} directly to disk file.\n")

    print("--- Phase 2: Simulating Unplanned System Crash & Reboot ---")
    # Simulate fresh in-memory database engine state post-crash
    kv_store: dict[str, str] = {}
    
    # Re-instantiate WAL engine to trigger log replay
    recovery_wal = WriteAheadLog(log_filename)
    
    print("[RECOVERY] Replaying WAL records to reconstruct in-memory state:")
    for entry in recovery_wal.replay():
        cmd = entry.command
        payload = entry.payload
        print(f"  Replaying LSN #{entry.lsn:02d} -> Action: {cmd} | Data: '{payload}'")
        
        if cmd == "SET_VAL":
            k, v = payload.split("=")
            kv_store[k] = v
        elif cmd == "DEL_VAL":
            kv_store.pop(payload, None)

    print("-" * 65)
    print(f"[SUCCESS] Reconstructed In-Memory Key-Value Store State: {kv_store}")import os
import struct
import zlib
from typing import Iterator

class WALEntry:
    """Represents a discrete mutation record formatted for binary serialization."""
    
    # Binary Payload Envelope: LSN (Q = uint64), Command (10s = 10 chars), Data Length (I = uint32)
    HEADER_FORMAT = "!Q10sI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, lsn: int, command: str, payload: str):
        self.lsn = lsn
        self.command = command.strip().ljust(10)  # Fixed-width 10-char string
        self.payload = payload.encode('utf-8')

    def serialize(self) -> bytes:
        """Serializes entry with a 32-bit CRC32 checksum appended at the end."""
        header = struct.pack(self.HEADER_FORMAT, self.lsn, self.command.encode('utf-8'), len(self.payload))
        record_body = header + self.payload
        checksum = zlib.crc32(record_body) & 0xFFFFFFFF
        return record_body + struct.pack("!I", checksum)

    @classmethod
    def deserialize_from_file(cls, file_obj) -> 'WALEntry | None':
        """Parses and validates a WAL record from a raw file stream."""
        header_bytes = file_obj.read(cls.HEADER_SIZE)
        if not header_bytes or len(header_bytes) < cls.HEADER_SIZE:
            return None  # End of log

        lsn, command_raw, payload_len = struct.unpack(cls.HEADER_FORMAT, header_bytes)
        payload = file_obj.read(payload_len)
        checksum_bytes = file_obj.read(4)

        if len(checksum_bytes) < 4:
            raise ValueError("Corrupted Log: Incomplete record checksum frame.")

        stored_checksum = struct.unpack("!I", checksum_bytes)[0]
        calculated_checksum = zlib.crc32(header_bytes + payload) & 0xFFFFFFFF

        if stored_checksum != calculated_checksum:
            raise ValueError(f"Corrupted Log: Checksum mismatch at LSN {lsn}!")

        command = command_raw.decode('utf-8').strip()
        return cls(lsn, command, payload.decode('utf-8'))


class WriteAheadLog:
    """Manages appending durable transactions and recovering state after a crash."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._next_lsn = 1
        
        # If file exists, scan to determine the highest active LSN
        if os.path.exists(filepath):
            for entry in self.replay():
                self._next_lsn = entry.lsn + 1

    def append(self, command: str, payload: str) -> int:
        """Appends a mutation to the log file and forces an explicit disk sync (fsync)."""
        entry = WALEntry(self._next_lsn, command, payload)
        serialized_bytes = entry.serialize()

        # Open in append-binary mode
        with open(self.filepath, "a+b") as f:
            f.write(serialized_bytes)
            f.flush()
            os.fsync(f.fileno())  # Force OS buffer cache commit to physical storage

        assigned_lsn = self._next_lsn
        self._next_lsn += 1
        return assigned_lsn

    def replay(self) -> Iterator[WALEntry]:
        """Reads through the WAL sequentially from start to end for crash recovery."""
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath, "rb") as f:
            while True:
                entry = WALEntry.deserialize_from_file(f)
                if entry is None:
                    break
                yield entry


if __name__ == "__main__":
    log_filename = "transactions.wal"
    
    # Cleanup previous run logs for clean execution
    if os.path.exists(log_filename):
        os.remove(log_filename)

    print("--- Phase 1: Operating Normal Transactions ---")
    wal = WriteAheadLog(log_filename)
    
    lsn1 = wal.append("SET_VAL", "user:101=Alice")
    lsn2 = wal.append("SET_VAL", "user:102=Bob")
    lsn3 = wal.append("DEL_VAL", "user:101")
    
    print(f"  [WAL] Appended LSNs {lsn1}, {lsn2}, {lsn3} directly to disk file.\n")

    print("--- Phase 2: Simulating Unplanned System Crash & Reboot ---")
    # Simulate fresh in-memory database engine state post-crash
    kv_store: dict[str, str] = {}
    
    # Re-instantiate WAL engine to trigger log replay
    recovery_wal = WriteAheadLog(log_filename)
    
    print("[RECOVERY] Replaying WAL records to reconstruct in-memory state:")
    for entry in recovery_wal.replay():
        cmd = entry.command
        payload = entry.payload
        print(f"  Replaying LSN #{entry.lsn:02d} -> Action: {cmd} | Data: '{payload}'")
        
        if cmd == "SET_VAL":
            k, v = payload.split("=")
            kv_store[k] = v
        elif cmd == "DEL_VAL":
            kv_store.pop(payload, None)

    print("-" * 65)
    print(f"[SUCCESS] Reconstructed In-Memory Key-Value Store State: {kv_store}")

# Output :
# --- Phase 1: Operating Normal Transactions ---
#   [WAL] Appended LSNs 1, 2, 3 directly to disk file.

# --- Phase 2: Simulating Unplanned System Crash & Reboot ---
# [RECOVERY] Replaying WAL records to reconstruct in-memory state:
#   Replaying LSN #01 -> Action: SET_VAL    | Data: 'b'user:101=Alice''
#   Replaying LSN #02 -> Action: SET_VAL    | Data: 'b'user:102=Bob''
#   Replaying LSN #03 -> Action: DEL_VAL    | Data: 'b'user:101''
# -----------------------------------------------------------------
# [SUCCESS] Reconstructed In-Memory Key-Value Store State: {}
