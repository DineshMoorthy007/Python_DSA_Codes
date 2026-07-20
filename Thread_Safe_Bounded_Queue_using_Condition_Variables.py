import threading
import time
from typing import Generic, TypeVar

T = TypeVar('T')

class BoundedBlockingQueue(Generic[T]):
    """A thread-safe FIFO queue bounded by a fixed maximum capacity.
    
    Blocks producers when capacity is full, and blocks consumers when queue is empty.
    """
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero.")
            
        self._capacity = capacity
        self._queue: list[T] = []
        
        # A single lock paired with condition variables for state signaling
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def enqueue(self, item: T, timeout: float | None = None) -> bool:
        """Puts an item into the queue. 
        
        If full, blocks until space becomes available or until timeout occurs.
        """
        with self._not_full:
            end_time = time.time() + timeout if timeout is not None else None
            
            # Wait while the queue remains at max capacity
            while len(self._queue) >= self._capacity:
                if timeout is not None:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return False  # Timed out waiting for space
                    self._not_full.wait(remaining)
                else:
                    self._not_full.wait()

            self._queue.append(item)
            # Signal any sleeping consumer threads that data is ready
            self._not_empty.notify()
            return True

    def dequeue(self, timeout: float | None = None) -> T | None:
        """Removes and returns an item from the queue.
        
        If empty, blocks until an item is available or until timeout occurs.
        """
        with self._not_empty:
            end_time = time.time() + timeout if timeout is not None else None
            
            # Wait while the queue contains zero elements
            while len(self._queue) == 0:
                if timeout is not None:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return None  # Timed out waiting for data
                    self._not_empty.wait(remaining)
                else:
                    self._not_empty.wait()

            item = self._queue.pop(0)
            # Signal any sleeping producer threads that space has cleared
            self._not_full.notify()
            return item

    def size(self) -> int:
        """Returns the current snapshot count of items in the queue."""
        with self._lock:
            return len(self._queue)


# --- Simulation Script ---

def producer_task(queue: BoundedBlockingQueue[str], total_items: int):
    for i in range(1, total_items + 1):
        item = f"Payload_{i}"
        print(f"[PRODUCER] Attempting to enqueue: {item}")
        queue.enqueue(item)
        print(f"  -->[PRODUCER SUCCESS] Enqueued: {item} (Queue Size: {queue.size()})")
        time.sleep(0.1)  # Simulate fast production work

def consumer_task(queue: BoundedBlockingQueue[str], total_items: int):
    for _ in range(total_items):
        time.sleep(0.4)  # Simulate slow processing work (forces producer to block!)
        item = queue.dequeue()
        print(f"      [CONSUMER SUCCESS] <-- Dequeued & Processed: {item} (Queue Size: {queue.size()})")


if __name__ == "__main__":
    print("--- Initializing Thread-Safe Bounded Blocking Queue ---")
    
    # Restrict queue capacity to 2 to trigger backpressure quickly
    shared_queue = BoundedBlockingQueue[str](capacity=2)
    items_to_process = 5

    # Spin up concurrent worker threads
    producer = threading.Thread(target=producer_task, args=(shared_queue, items_to_process))
    consumer = threading.Thread(target=consumer_task, args=(shared_queue, items_to_process))

    print("\n[STARTING THREADS] Consumer processes slower than Producer...\n")
    consumer.start()
    producer.start()

    producer.join()
    consumer.join()
    print("\n[SUCCESS] Pipeline execution finished cleanly with zero race conditions.")

# Output :
# Initializing Thread-Safe Bounded Blocking Queue

# [STARTING THREADS] Consumer processes slower than Producer ...

# [PRODUCER] Attempting to enqueue: Payload_1
# -- >[PRODUCER SUCCESS] Enqueued: Payload_1 (Queue Size: 1)
# [PRODUCER] Attempting to enqueue: Payload_2
# -- >[PRODUCER SUCCESS] Enqueued: Payload_2 (Queue Size: 2)
# [PRODUCER] Attempting to enqueue: Payload_3
#     [CONSUMER SUCCESS] <-- Dequeued & Processed: Payload_1 (Queue Size: 1)
# -- >[PRODUCER SUCCESS] Enqueued: Payload_3 (Queue Size: 2)
# [PRODUCER] Attempting to enqueue: Payload_4
#     [CONSUMER SUCCESS] <-- Dequeued & Processed: Payload_2 (Queue Size: 1)
# -- >[PRODUCER SUCCESS] Enqueued: Payload_4 (Queue Size: 2)
# [PRODUCER] Attempting to enqueue: Payload_5
#     [CONSUMER SUCCESS] <-- Dequeued & Processed: Payload_3 (Queue Size: 1)
# -- >[PRODUCER SUCCESS] Enqueued: Payload_5 (Queue Size: 2)
#     [CONSUMER SUCCESS] <-- Dequeued & Processed: Payload_4 (Queue Size: 1)
#     [CONSUMER SUCCESS] <-- Dequeued & Processed: Payload_5 (Queue Size: 0)

# [SUCCESS] Pipeline execution finished cleanly with zero race conditions.
