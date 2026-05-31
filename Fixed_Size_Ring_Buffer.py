class CircularBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None] * capacity  # Pre-allocate fixed memory layout
        self.head = 0  # Pointer for pulling data out (Read)
        self.tail = 0  # Pointer for writing data in (Write)
        self.size = 0  # Keep track of active element count

    def enqueue(self, item):
        """Writes data to the tail pointer location, overwriting if full."""
        self.buffer[self.tail] = item
        
        if self.size == self.capacity:
            # If full, the head (oldest item) is pushed forward to make room
            self.head = (self.head + 1) % self.capacity
            print(f"[OVERWRITE] Buffer full! Added: {item} (Oldest element lost)")
        else:
            self.size += 1
            print(f"[WRITE] Enqueued item: {item}")
            
        # Standard step: Advance tail pointer and wrap around if at end
        self.tail = (self.tail + 1) % self.capacity

    def dequeue(self):
        """Reads and removes the oldest item from the head pointer."""
        if self.size == 0:
            return "[EMPTY] Cannot dequeue from an empty buffer."
            
        item = self.buffer[self.head]
        self.buffer[self.head] = None  # Clear memory slot
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return f"  [READ] Dequeued item: {item}"

    def __str__(self):
        return f"Buffer Array: {self.buffer} | Head at: {self.head} | Tail at: {self.tail}"

print("--- Initializing 3-Slot Ring Buffer ---")
stream = CircularBuffer(capacity=3)

stream.enqueue("Packet_A")
stream.enqueue("Packet_B")
stream.enqueue("Packet_C")
print(stream)

print("\n--- Overwriting Data (No Memory Expansion) ---")
stream.enqueue("Packet_D")  # Overwrites Packet_A
print(stream)

print("\n--- Consuming Data streams ---")
print(stream.dequeue())
print(stream.dequeue())
print(stream)

# Output :
# --- Initializing 3-Slot Ring Buffer ---
# [WRITE] Enqueued item: Packet_A
# [WRITE] Enqueued item: Packet_B
# [WRITE] Enqueued item: Packet_C
# Buffer Array: ['Packet_A', 'Packet_B', 'Packet_C'] | Head at: 0 | Tail at: 0

# --- Overwriting Data (No Memory Expansion) ---
# [OVERWRITE] Buffer full! Added: Packet_D (Oldest element lost)
# Buffer Array: ['Packet_D', 'Packet_B', 'Packet_C'] | Head at: 1 | Tail at: 1

# --- Consuming Data streams ---
#   [READ] Dequeued item: Packet_B
#   [READ] Dequeued item: Packet_C
# Buffer Array: ['Packet_D', None, None] | Head at: 0 | Tail at: 1
