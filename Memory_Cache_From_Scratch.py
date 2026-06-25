class ListNode:
    """A node inside a doubly linked list structure."""
    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev: ListNode | None = None
        self.next: ListNode | None = None


class LRUCache:
    """An O(1) Least Recently Used Cache implementation."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        # Hash map associates keys directly to list node references
        self.cache: dict[int, ListNode] = {}
        
        # Initialize sentinel pseudo head and tail nodes to avoid null-pointer checks
        self.head = ListNode()
        self.tail = ListNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: ListNode) -> None:
        """Internal helper to isolate and un-link a node from the chain."""
        prev_node = node.prev
        next_node = node.next
        if prev_node and next_node:
            prev_node.next = next_node
            next_node.prev = prev_node

    def _add_to_head(self, node: ListNode) -> None:
        """Internal helper to anchor an active node immediately behind the head pointer."""
        node.prev = self.head
        node.next = self.head.next
        
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        """Fetches a value from the cache. Moves accessed element to the head."""
        if key in self.cache:
            node = self.cache[key]
            # Since this item was just read, refresh its recency
            self._remove(node)
            self._add_to_head(node)
            return node.value
        return -1  # Cache Miss

    def put(self, key: int, value: int) -> None:
        """Inserts or updates a value. Evicts the oldest node if capacity is breached."""
        if key in self.cache:
            # Key exists: Update value and move it to the front
            node = self.cache[key]
            node.value = value
            self._remove(node)
            self._add_to_head(node)
        else:
            # New Entry: Create node and register it in the dictionary
            new_node = ListNode(key, value)
            self.cache[key] = new_node
            self._add_to_head(new_node)
            
            # Capacity check: If overflowing, evict the tail node
            if len(self.cache) > self.capacity:
                # The oldest item always sits right before the sentinel tail node
                oldest_node = self.tail.prev
                if oldest_node and oldest_node != self.head:
                    self._remove(oldest_node)
                    # Clear it from the hash map lookup registry
                    del self.cache[oldest_node.key]


if __name__ == "__main__":
    print("--- Initializing Dynamic LRU Memory Cache ---")
    # Spin up a small cache that can only hold 2 active values
    memory_pool = LRUCache(capacity=2)
    
    print("Action: Populate Cache with Keys")
    memory_pool.put(1, 100)
    memory_pool.put(2, 200)
    
    print(f"  Lookup Key 1 -> Value: {memory_pool.get(1)} (Key 1 becomes Most Recent)")
    
    print("Action: Insert Key 3 (Triggers Capacity Limit Eviction)")
    memory_pool.put(3, 300)  # Evicts Key 2 because Key 1 was refreshed recently!
    
    print("-" * 55)
    print(f"[VERIFY] Checking Key 2 (Evicted)   -> Result: {memory_pool.get(2)}")
    print(f"[VERIFY] Checking Key 1 (Preserved) -> Result: {memory_pool.get(1)}")
    print(f"[VERIFY] Checking Key 3 (Preserved) -> Result: {memory_pool.get(3)}")

# Output :
# --- Initializing Dynamic LRU Memory Cache ---
# Action: Populate Cache with Keys
#   Lookup Key 1 -> Value: 100 (Key 1 becomes Most Recent)
# Action: Insert Key 3 (Triggers Capacity Limit Eviction)
# -------------------------------------------------------
# [VERIFY] Checking Key 2 (Evicted)   -> Result: -1
# [VERIFY] Checking Key 1 (Preserved) -> Result: 100
# [VERIFY] Checking Key 3 (Preserved) -> Result: 300
