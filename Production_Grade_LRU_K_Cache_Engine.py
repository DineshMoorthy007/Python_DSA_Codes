import time

class LRUKNode:
    """A cache page tracking its payload and access history timestamps."""
    def __init__(self, key: int, value: int, k: int):
        self.key = key
        self.value = value
        self.k = k
        # Stores historical access timestamps (capped at max length k)
        self.history: list[float] = [time.time()]

    def record_access(self) -> None:
        """Appends current timestamp and drops older entries past boundary k."""
        self.history.append(time.time())
        if len(self.history) > self.k:
            self.history.pop(0)

    def get_k_distance(self, current_time: float) -> float:
        """Calculates backward distance to the k-th previous access.
        
        If fewer than k accesses exist, distance is infinite float('inf').
        """
        if len(self.history) < self.k:
            return float('inf')
        return current_time - self.history[0]


class LRUKCache:
    """An LRU-K Cache Engine protecting hot records from sequential scans."""
    def __init__(self, capacity: int, k: int = 2):
        self.capacity = capacity
        self.k = k
        self.cache: dict[int, LRUKNode] = {}

    def get(self, key: int) -> int:
        """Retrieves a cached value and updates its access history."""
        if key not in self.cache:
            return -1  # Cache Miss

        node = self.cache[key]
        node.record_access()
        return node.value

    def put(self, key: int, value: int) -> None:
        """Inserts or updates a value. Evicts the item with maximum k-distance."""
        current_time = time.time()

        if key in self.cache:
            node = self.cache[key]
            node.value = value
            node.record_access()
            return

        # Capacity full: Evict candidate with the maximum backward k-distance
        if len(self.cache) >= self.capacity:
            evict_key = None
            max_k_distance = -1.0

            for k_key, node in self.cache.items():
                distance = node.get_k_distance(current_time)
                
                # Items with distance = inf (fewer than k accesses) take top eviction priority
                if distance > max_k_distance:
                    max_k_distance = distance
                    evict_key = k_key

            if evict_key is not None:
                print(f"  [EVICTION] Evicted Key '{evict_key}' (k-distance: {max_k_distance})")
                del self.cache[evict_key]

        # Add new key
        new_node = LRUKNode(key, value, self.k)
        self.cache[key] = new_node


if __name__ == "__main__":
    print("--- Initializing Scan-Resistant LRU-2 Cache Engine ---")
    
    # Create cache capped at 3 items using K=2
    cache = LRUKCache(capacity=3, k=2)

    # 1. Access keys repeatedly to make them "Hot" (>= 2 accesses)
    cache.put(101, 1000)
    cache.get(101)  # Key 101 now has 2 accesses (Hot status)

    cache.put(102, 2000)
    cache.get(102)  # Key 102 now has 2 accesses (Hot status)

    # Key 103 has only 1 access (Cold status)
    cache.put(103, 3000)

    print("\n[CACHE STATE] Keys 101 & 102 are Hot (2+ hits). Key 103 is Cold (1 hit).")
    print("-" * 65)

    # 2. Simulate a sequential scan insertion (Key 999)
    # Standard LRU would evict Key 101, but LRU-K evicts Cold Key 103 instead!
    print("[SCAN DETECTED] Inserting new item (Key 999)...")
    cache.put(999, 9999)

    print("\n[VERIFICATION]")
    print(f"Key 101 (Hot Key) Still in Cache? -> {cache.get(101) != -1}")
    print(f"Key 103 (Cold Key) Evicted?      -> {cache.get(103) == -1}")

# Output :
# --- Initializing Scan-Resistant LRU-2 Cache Engine ---

# [CACHE STATE] Keys 101 & 102 are Hot (2+ hits). Key 103 is Cold (1 hit).
# -----------------------------------------------------------------
# [SCAN DETECTED] Inserting new item (Key 999)...
#   [EVICTION] Evicted Key '103' (k-distance: inf)

# [VERIFICATION]
# Key 101 (Hot Key) Still in Cache? -> True
# Key 103 (Cold Key) Evicted?      -> True
