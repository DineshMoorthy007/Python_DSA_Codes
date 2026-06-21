import threading
import time
import random
from collections import deque

class BoundedBuffer:
    """A thread-safe, size-limited buffer for worker synchronization."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque()
        
        # Core synchronization primitives
        self.lock = threading.Lock()
        # Condition variables linked to our main structural lock
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)

    def enqueue(self, item: int, worker_name: str) -> None:
        """Adds an item to the queue. Blocks if the buffer is entirely full."""
        with self.not_full:
            # Wait while the buffer is at maximum capacity
            while len(self.buffer) == self.capacity:
                print(f"  [WAIT] {worker_name} is waiting... Buffer is FULL.")
                self.not_full.wait()
            
            # Commit item to memory
            self.buffer.append(item)
            print(f"[PRODUCE] {worker_name} generated task: {item} (Size: {len(self.buffer)})")
            
            # Wake up any sleeping consumers waiting for data
            self.not_empty.notify()

    def dequeue(self, worker_name: str) -> int:
        """Removes an item from the queue. Blocks if the buffer is empty."""
        with self.not_empty:
            # Wait while there are zero tasks to process
            while len(self.buffer) == 0:
                print(f"  [WAIT] {worker_name} is waiting... Buffer is EMPTY.")
                self.not_empty.wait()
            
            # Extract item from the front of the queue
            item = self.buffer.popleft()
            print(f"  [CONSUME] {worker_name} processed task: {item} (Size: {len(self.buffer)})")
            
            # Wake up any sleeping producers waiting for capacity space
            self.not_full.notify()
            return item


# --- Worker Threads ---

def producer(buffer: BoundedBuffer, count: int, name: str):
    for _ in range(count):
        time.sleep(random.uniform(0.1, 0.4))  # Simulate active data gathering
        task_id = random.randint(1000, 9999)
        buffer.enqueue(task_id, name)

def consumer(buffer: BoundedBuffer, count: int, name: str):
    for _ in range(count):
        time.sleep(random.uniform(0.3, 0.6))  # Simulate heavy processing overhead
        buffer.dequeue(name)


if __name__ == "__main__":
    print("--- Initializing Concurrency Sync Engine ---")
    # Restrict memory pool capacity to a max of 3 elements
    shared_buffer = BoundedBuffer(capacity=3)

    # Creating active, independent concurrent thread tracks
    p1 = threading.Thread(target=producer, args=(shared_buffer, 5, "Producer_Alpha"))
    c1 = threading.Thread(target=consumer, args=(shared_buffer, 5, "Consumer_Omega"))

    p1.start()
    c1.start()

    p1.join()
    c1.join()
    
    print("-" * 47)
    print("[SUCCESS] All concurrent worker threads finished execution.")
