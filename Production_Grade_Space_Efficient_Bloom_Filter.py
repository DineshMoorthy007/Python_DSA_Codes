import math
import mmh3
import hashlib

class BloomFilter:
    """A space-efficient probabilistic data structure for set membership testing."""
    def __init__(self, expected_elements: int, false_positive_rate: float):
        if not (0 < false_positive_rate < 1):
            raise ValueError("False positive rate must be strictly between 0 and 1.")
            
        self.n = expected_elements
        self.p = false_positive_rate

        # Formula 1: Optimal bit array size (m) = - (n * ln(p)) / (ln(2)^2)
        self.size = int(- (self.n * math.log(self.p)) / (math.log(2) ** 2))

        # Formula 2: Optimal number of hash functions (k) = (m / n) * ln(2)
        self.hash_count = max(1, int((self.size / self.n) * math.log(2)))

        # Allocate underlying bit array initialized to 0
        self.bit_array = [0] * self.size

    def _hashes(self, item: str):
        """Generates 'k' hash indexes using double-hashing technique."""
        # Primary hash via MurmurHash3
        h1 = mmh3.hash(item)
        # Secondary hash via SHA-256
        h2 = int(hashlib.sha256(item.encode('utf-8')).hexdigest(), 16)

        for i in range(self.hash_count):
            # Kirsch-Mitzenmacher formula: g_i(x) = (h1(x) + i * h2(x)) % size
            yield (h1 + i * h2) % self.size

    def add(self, item: str) -> None:
        """Adds an item to the Bloom Filter by setting target bits to 1."""
        for bit_index in self._hashes(item):
            self.bit_array[bit_index] = 1

    def contains(self, item: str) -> bool:
        """Checks for membership in the filter.
        
        Returns:
            False -> Item DEFINITELY does NOT exist in the set.
            True  -> Item PROBABLY exists (subject to false-positive rate).
        """
        for bit_index in self._hashes(item):
            if self.bit_array[bit_index] == 0:
                return False  # If even a single bit is 0, the item was NEVER added!
        return True


if __name__ == "__main__":
    print("--- Initializing Space-Optimized Bloom Filter ---")
    
    # Configure filter for 100,000 items with a max 1% (0.01) false-positive threshold
    bloom = BloomFilter(expected_elements=100_000, false_positive_rate=0.01)
    
    print(f"Allocated Bit Array Size : {bloom.size:,} bits (~{bloom.size / 8 / 1024:.2f} KB)")
    print(f"Calculated Hash Functions: {bloom.hash_count} passes")
    print("-" * 60)

    # Ingest existing records
    registered_users = ["alice_99", "bob_dev", "charlie_core"]
    for user in registered_users:
        bloom.add(user)

    # Verification passes
    print(f"Lookup 'alice_99'     (Registered)  -> Probably Exists? : {bloom.contains('alice_99')}")
    print(f"Lookup 'unknown_user' (Unregistered) -> Probably Exists? : {bloom.contains('unknown_user')}")

# Output :
# --- Initializing Space-Optimized Bloom Filter ---
# Allocated Bit Array Size : 958,505 bits (~117.01 KB)
# Calculated Hash Functions: 6 passes
# ------------------------------------------------------------
# Lookup 'alice_99'     (Registered)  -> Probably Exists? : True
# Lookup 'unknown_user' (Unregistered) -> Probably Exists? : False
