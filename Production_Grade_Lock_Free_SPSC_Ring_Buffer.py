import time
from multiprocessing import Process, Value, Array

class LockFreeSPSCBuffer:
    """A thread-safe, lock-free Single-Producer Single-Consumer ring buffer.
    
    Eliminates mutex contention by leveraging atomic head/tail index tracking.
    """
    def __init__(self, capacity: int):
        # Power-of-two capacity enables fast bitwise masking instead of slow modulo
        if (capacity & (capacity - 1)) != 0 or capacity <= 0:
            raise ValueError("Capacity must be a power of two (e.g., 8, 16, 32).")
            
        self.capacity = capacity
        self.mask = capacity - 1
        
        # Shared memory ring storage array (pre-allocated)
        self._buffer = Array('i', [0] * capacity)
        
        # Atomic pointers for thread synchronization
        self._head = Value('i', 0)  # Written ONLY by Producer
        self._tail = Value('i', 0)  # Written ONLY by Consumer

    def push(self, item: int) -> bool:
        """Producer API: Pushes an integer into the buffer.
        
        Returns False if the buffer is full (backpressure boundary).
        """
        head = self._head.value
        tail = self._tail.value  # Read atomic tail pointer

        # Buffer Full Condition: Head index is capacity steps ahead of tail
        if head - tail >= self.capacity:
            return False

        # Write data to circular index using bitwise mask
        self._buffer[head & self.mask] = item
        
        # Atomic commit: Update head pointer
        self._head.value = head + 1
        return True

    def pop(self) -> int | None:
        """Consumer API: Removes and returns an item from the buffer.
        
        Returns None if the buffer is empty.
        """
        tail = self._tail.value
        head = self._head.value  # Read atomic head pointer

        # Buffer Empty Condition: Tail pointer matches head pointer
        if tail == head:
            return None

        # Extract item from circular index
        item = self._buffer[tail & self.mask]
        
        # Atomic commit: Update tail pointer
        self._tail.value = tail + 1
        return item


# --- Concurrent Multi-Processing Benchmark ---

def producer_process(ring: LockFreeSPSCBuffer, item_count: int):
    """Producer task running on an isolated CPU process."""
    for i in range(1, item_count + 1):
        while not ring.push(i):
            # Buffer full: Yield brief CPU spin-wait
            pass
    print(f"  [PRODUCER] Successfully dispatched {item_count:,} items.")

def consumer_process(ring: LockFreeSPSCBuffer, item_count: int):
    """Consumer task running on an isolated CPU process."""
    received = 0
    while received < item_count:
        val = ring.pop()
        if val is not None:
            received += 1
        else:
            # Buffer empty: Yield brief CPU spin-wait
            pass
    print(f"  [CONSUMER] Successfully processed {received:,} items.")


if __name__ == "__main__":
    print("--- Initializing High-Speed SPSC Lock-Free Ring Buffer ---\n")

    total_events = 500_000
    buffer_capacity = 1024  # Power of two ring size
    
    ring = LockFreeSPSCBuffer(capacity=buffer_capacity)

    p_producer = Process(target=producer_process, args=(ring, total_events))
    p_consumer = Process(target=consumer_process, args=(ring, total_events))

    start_time = time.perf_counter()

    p_consumer.start()
    p_producer.start()

    p_producer.join()
    p_consumer.join()

    elapsed = time.perf_counter() - start_time

    print("-" * 60)
    print("[BENCHMARK COMPLETED]")
    print(f"  Total Messages Transferred : {total_events:,}")
    print(f"  Execution Time             : {elapsed:.3f} seconds")
    print(f"  Throughput                 : {total_events / elapsed:,.0f} ops/sec")

# Output :
# --- Initializing High-Speed SPSC Lock-Free Ring Buffer ---

#   [CONSUMER] Successfully processed 500,000 items.  [PRODUCER] Successfully dispatched 500,000 items.

# ------------------------------------------------------------
# [BENCHMARK COMPLETED]
#   Total Messages Transferred : 500,000
#   Execution Time             : 7.922 seconds
#   Throughput                 : 63,119 ops/sec
