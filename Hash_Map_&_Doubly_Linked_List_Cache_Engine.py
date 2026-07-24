class CacheNode:
    """A node in the doubly linked list storing cache keys and values."""
    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev: CacheNode | None = None
        self.next: CacheNode | None = None


class LRUCache:
    """A thread-safe-ready LRU Cache achieving O(1) reads, updates, and evictions."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        # Hash map maps keys directly to list node pointers
        self.cache: dict[int, CacheNode] = {}
        
        # Sentinel dummy nodes anchor the boundaries of our list
        self.head = CacheNode()  # Most Recently Used (MRU) boundary
        self.tail = CacheNode()  # Least Recently Used (LRU) boundary
        
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove_node(self, node: CacheNode) -> None:
        """Unlinks a node from its current position in the doubly linked list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _add_to_head(self, node: CacheNode) -> None:
        """Inserts a node right after the head sentinel (MRU position)."""
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        """Retrieves a cached value and promotes the node to MRU status."""
        if key not in self.cache:
            return -1  # Cache miss

        node = self.cache[key]
        # Promote accessed node to the front (Most Recently Used)
        self._remove_node(node)
        self._add_to_head(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        """Inserts or updates a value. Evicts the LRU node if capacity is breached."""
        if key in self.cache:
            # Key exists: update its value and move to front
            node = self.cache[key]
            node.value = value
            self._remove_node(node)
            self._add_to_head(node)
        else:
            # Check capacity limits before inserting new key
            if len(self.cache) >= self.capacity:
                # Evict the Least Recently Used node (just before tail sentinel)
                lru_node = self.tail.prev
                self._remove_node(lru_node)
                del self.cache[lru_node.key]
                print(f"  [EVICTION] Capacity reached! Evicted key '{lru_node.key}'")

            # Allocate new node and insert at head
            new_node = CacheNode(key, value)
            self.cache[key] = new_node
            self._add_to_head(new_node)


if __name__ == "__main__":
    print("--- Initializing High-Speed LRU Cache Engine ---")
    
    # Instantiate an LRU cache capped at 2 elements
    lru = LRUCache(capacity=2)

    lru.put(1, 100)  # Cache: {1}
    lru.put(2, 200)  # Cache: {2, 1} (2 is MRU, 1 is LRU)
    print(f"Lookup Key 1 -> Value: {lru.get(1)}")  # Accessing 1 promotes it! Cache: {1, 2}

    print("-" * 55)
    # Inserting key 3 triggers eviction because capacity (2) is full
    lru.put(3, 300)  # Key 2 was LRU, so it gets dropped! Cache: {3, 1}

    print(f"Lookup Key 2 (Evicted) -> Result: {lru.get(2)}")  # Returns -1 (Cache Miss)
    print(f"Lookup Key 3 (Active)  -> Result: {lru.get(3)}")   # Returns 300

# Output :
# --- Initializing High-Speed LRU Cache Engine ---
# Lookup Key 1 -> Value: 100
# -------------------------------------------------------
#   [EVICTION] Capacity reached! Evicted key '2'
# Lookup Key 2 (Evicted) -> Result: -1
# Lookup Key 3 (Active)  -> Result: 300
