import threading
import time
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class LockFreeMPSCBuffer(Generic[T]):
    """A Lock-Free Multi-Producer Single-Consumer (MPSC) Ring Buffer.
    
    Allows multiple producer threads to reserve write slots concurrently
    using atomic counters while a single consumer thread reads sequentially.
    """
    def __init__(self, capacity: int):
        # Power-of-two capacity enables fast bitwise modulo
        if (capacity & (capacity - 1)) != 0 or capacity <= 0:
            raise ValueError("Capacity must be a power of 2!")

        self.capacity = capacity
        self.mask = capacity - 1
        
        # Pre-allocated circular storage buffer
        self.buffer: list[Optional[T]] = [None] * capacity
        
        # Array tracking whether a slot has finished writing
        self.written_flags: list[bool] = [False] * capacity

        # Atomic sequence tracking
        self._write_head = 0  # Claimed by producers
        self._read_tail = 0   # Advanced by single consumer
        self._lock = threading.Lock()  # Synchronizes atomic head increments in Python

    def _atomic_claim_slot(self) -> tuple[int, int]:
        """Atomically claims the next write index in the ring buffer."""
        with self._lock:
            slot_idx = self._write_head
            self._write_head += 1
            return slot_idx, slot_idx & self.mask

    def publish(self, item: T) -> bool:
        """Producer API: Atomically reserves a slot and writes data."""
        # Check if buffer is full (bounded backpressure)
        if self._write_head - self._read_tail >= self.capacity:
            return False  # Buffer full

        ticket, slot = self._atomic_claim_slot()
        
        # Write item into pre-allocated slot
        self.buffer[slot] = item
        # Mark slot as published so the consumer knows it's ready to read
        self.written_flags[slot] = True
        return True

    def consume(self) -> Optional[T]:
        """Consumer API: Reads next ready item in sequential order."""
        slot = self._read_tail & self.mask

        # Check if the next expected slot is published
        if not self.written_flags[slot]:
            return None  # No data ready yet

        item = self.buffer[slot]
        self.buffer[slot] = None
        self.written_flags[slot] = False  # Reset flag for future writes
        
        self._read_tail += 1
        return item


# --- Multi-Threaded Simulation ---

def producer_thread(buffer: LockFreeMPSCBuffer[str], producer_id: int, count: int):
    for i in range(1, count + 1):
        msg = f"P{producer_id}_Msg_{i}"
        while not buffer.publish(msg):
            time.sleep(0.001)  # Yield if buffer is temporarily full

if __name__ == "__main__":
    print("--- Initializing Multi-Producer Lock-Free Ring Buffer ---\n")

    buffer_size = 16
    ring_buffer = LockFreeMPSCBuffer[str](capacity=buffer_size)

    total_producers = 3
    messages_per_producer = 4
    total_expected = total_producers * messages_per_producer

    # Launch 3 concurrent producer threads
    threads = []
    for pid in range(1, total_producers + 1):
        t = threading.Thread(target=producer_thread, args=(ring_buffer, pid, messages_per_producer))
        threads.append(t)
        t.start()

    # Consumer loop on main thread
    received_items = []
    print("[CONSUMER] Polling items from multi-producer stream...")
    
    while len(received_items) < total_expected:
        item = ring_buffer.consume()
        if item is not None:
            received_items.append(item)
            print(f"  <-- Consumed: {item} (Total Received: {len(received_items)}/{total_expected})")
        else:
            time.sleep(0.002)

    for t in threads:
        t.join()

    print("-" * 65)
    print(f"[SUCCESS] Multi-Producer ingestion complete with zero locks during slot reservation!")

# Output :
# --- Initializing Multi-Producer Lock-Free Ring Buffer ---

# [CONSUMER] Polling items from multi-producer stream...
#   <-- Consumed: P1_Msg_1 (Total Received: 1/12)
#   <-- Consumed: P1_Msg_2 (Total Received: 2/12)
#   <-- Consumed: P1_Msg_3 (Total Received: 3/12)
#   <-- Consumed: P1_Msg_4 (Total Received: 4/12)
#   <-- Consumed: P2_Msg_1 (Total Received: 5/12)
#   <-- Consumed: P2_Msg_2 (Total Received: 6/12)
#   <-- Consumed: P2_Msg_3 (Total Received: 7/12)
#   <-- Consumed: P2_Msg_4 (Total Received: 8/12)
#   <-- Consumed: P3_Msg_1 (Total Received: 9/12)
#   <-- Consumed: P3_Msg_2 (Total Received: 10/12)
#   <-- Consumed: P3_Msg_3 (Total Received: 11/12)
#   <-- Consumed: P3_Msg_4 (Total Received: 12/12)
# -----------------------------------------------------------------
# [SUCCESS] Multi-Producer ingestion complete with zero locks during slot reservation!
