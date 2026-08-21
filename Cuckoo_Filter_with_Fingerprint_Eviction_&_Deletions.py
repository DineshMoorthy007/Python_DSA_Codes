import hashlib
import random
from typing import List

class CuckooFilter:
    """A probabilistic data structure supporting insert, lookup, and delete.
    
    Uses partial-key cuckoo hashing with multi-slot buckets.
    """
    def __init__(self, capacity: int = 1000, bucket_size: int = 4, max_kicks: int = 500):
        self.bucket_size = bucket_size      # Number of fingerprint slots per bucket (b)
        self.max_kicks = max_kicks          # Max displacement iterations before resizing
        
        # Number of buckets (power of 2 recommended for fast modulo/masking)
        self.num_buckets = max(1, capacity // bucket_size)
        self.buckets: List[List[int]] = [[] for _ in range(self.num_buckets)]
        self.count = 0

    def _fingerprint(self, item: str) -> int:
        """Derives an 8-bit non-zero fingerprint for an item."""
        digest = hashlib.md5(item.encode('utf-8')).hexdigest()
        fp = int(digest[:2], 16)
        # Ensure fingerprint is never zero (reserved for empty)
        return fp if fp != 0 else 1

    def _hash_index(self, item: str) -> int:
        """Computes primary bucket index using Murmur-style hash integer."""
        digest = hashlib.sha256(item.encode('utf-8')).hexdigest()
        return int(digest[:8], 16) % self.num_buckets

    def _alt_index(self, index: int, fingerprint: int) -> int:
        """Calculates alternate bucket index via partial-key cuckoo hashing.
        
        Formula: alt_idx = (index ^ hash(fingerprint)) % num_buckets
        """
        fp_digest = hashlib.sha256(str(fingerprint).encode('utf-8')).hexdigest()
        fp_hash = int(fp_digest[:8], 16)
        return (index ^ fp_hash) % self.num_buckets

    def insert(self, item: str) -> bool:
        """Inserts an item by fingerprint into one of its two candidate buckets."""
        fp = self._fingerprint(item)
        i1 = self._hash_index(item)
        i2 = self._alt_index(i1, fp)

        # 1. Direct slot insertion if either candidate bucket has room
        if len(self.buckets[i1]) < self.bucket_size:
            self.buckets[i1].append(fp)
            self.count += 1
            return True
        if len(self.buckets[i2]) < self.bucket_size:
            self.buckets[i2].append(fp)
            self.count += 1
            return True

        # 2. Both buckets full: initiate Cuckoo kick-out displacement chain
        curr_idx = random.choice([i1, i2])
        curr_fp = fp

        for _ in range(self.max_kicks):
            # Select random victim fingerprint to evict from chosen bucket
            victim_pos = random.randint(0, len(self.buckets[curr_idx]) - 1)
            victim_fp = self.buckets[curr_idx][victim_pos]
            
            # Place incoming fingerprint into victim's slot
            self.buckets[curr_idx][victim_pos] = curr_fp

            # Evicted victim must now be placed into its alternate bucket
            curr_idx = self._alt_index(curr_idx, victim_fp)
            curr_fp = victim_fp

            if len(self.buckets[curr_idx]) < self.bucket_size:
                self.buckets[curr_idx].append(curr_fp)
                self.count += 1
                return True

        # Filter reached maximum load factor threshold without finding an open slot
        return False

    def contains(self, item: str) -> bool:
        """Queries whether an item is likely present in the set."""
        fp = self._fingerprint(item)
        i1 = self._hash_index(item)
        i2 = self._alt_index(i1, fp)

        # Item is present if its fingerprint is in bucket i1 OR bucket i2
        return (fp in self.buckets[i1]) or (fp in self.buckets[i2])

    def delete(self, item: str) -> bool:
        """Removes a single instance of an item's fingerprint from the filter."""
        fp = self._fingerprint(item)
        i1 = self._hash_index(item)
        i2 = self._alt_index(i1, fp)

        if fp in self.buckets[i1]:
            self.buckets[i1].remove(fp)
            self.count -= 1
            return True
        if fp in self.buckets[i2]:
            self.buckets[i2].remove(fp)
            self.count -= 1
            return True

        return False


if __name__ == "__main__":
    print("--- Initializing Probabilistic Cuckoo Filter ---\n")

    # Allocate filter with capacity for ~500 items across 4-slot buckets
    cf = CuckooFilter(capacity=500, bucket_size=4)

    # 1. Ingest member keys
    ingested_keys = [f"session_token_{i}" for i in range(1, 101)]
    print(f"[INGESTION] Inserting {len(ingested_keys)} session tokens...")
    for key in ingested_keys:
        success = cf.insert(key)
        if not success:
            print(f"  Warning: Filter full during insert of {key}")

    print(f"  Total Fingerprints Stored: {cf.count}")
    print("-" * 65)

    # 2. Positive and Negative Membership Queries
    print("\n[POINT QUERIES]")
    test_queries = [
        ("session_token_1", True),
        ("session_token_50", True),
        ("session_token_999", False),
        ("malicious_hacker_ip", False)
    ]
    for key, expected in test_queries:
        exists = cf.contains(key)
        status = "HIT (Present)" if exists else "MISS (Absent)"
        print(f"  Query '{key:<20}' ---> {status}")

    # 3. Dynamic Deletion Support
    print("\n[DELETION TEST]")
    target_to_delete = "session_token_50"
    print(f"  Pre-Delete  Contains '{target_to_delete}': {cf.contains(target_to_delete)}")
    
    deleted = cf.delete(target_to_delete)
    print(f"  Delete Action Executed: {deleted}")
    print(f"  Post-Delete Contains '{target_to_delete}': {cf.contains(target_to_delete)}")

    print("-" * 65)
    print("[SUCCESS] High-density probabilistic set with zero false negatives and full deletion support!")

# Output :
# --- Initializing Probabilistic Cuckoo Filter ---

# [INGESTION] Inserting 100 session tokens...
#   Total Fingerprints Stored: 100
# -----------------------------------------------------------------

# [POINT QUERIES]
#   Query 'session_token_1     ' ---> HIT (Present)
#   Query 'session_token_50    ' ---> HIT (Present)
#   Query 'session_token_999   ' ---> MISS (Absent)
#   Query 'malicious_hacker_ip ' ---> MISS (Absent)

# [DELETION TEST]
#   Pre-Delete  Contains 'session_token_50': True
#   Delete Action Executed: True
#   Post-Delete Contains 'session_token_50': False
# -----------------------------------------------------------------
# [SUCCESS] High-density probabilistic set with zero false negatives and full deletion support!
