import bisect
from typing import Optional, List, Tuple

class SSTableSegment:
    """An immutable, on-disk sorted string table segment."""
    def __init__(self, segment_id: int, entries: List[Tuple[str, Optional[str]]]):
        self.segment_id = segment_id
        # Sorted keys and values
        self.keys = [k for k, _ in entries]
        self.values = [v for _, v in entries]

    def get(self, key: str) -> Tuple[bool, Optional[str]]:
        """Searches the sorted segment for a key using binary search in O(log N) time.
        
        Returns:
            (found, value): where value=None signifies an explicit deleted tombstone.
        """
        idx = bisect.bisect_left(self.keys, key)
        if idx < len(self.keys) and self.keys[idx] == key:
            return True, self.values[idx]
        return False, None


class LSMTree:
    """A minimal Log-Structured Merge-Tree storage engine."""
    
    def __init__(self, memtable_threshold: int = 3):
        self.threshold = memtable_threshold
        # In-memory mutable sorted buffer (MemTable)
        self.memtable: dict[str, Optional[str]] = {}
        # Immutable on-disk SSTable segments (newest segments at index 0)
        self.segments: List[SSTableSegment] = []
        self._segment_counter = 0

    def put(self, key: str, value: str) -> None:
        """Inserts or updates a key-value pair."""
        self.memtable[key] = value
        self._check_flush()

    def delete(self, key: str) -> None:
        """Appends a deletion marker (tombstone) for the specified key."""
        # Deletions are treated as writes with a None (tombstone) value
        self.memtable[key] = None
        self._check_flush()

    def _check_flush(self) -> None:
        """Flushes MemTable to a new immutable SSTable if threshold is reached."""
        if len(self.memtable) >= self.threshold:
            self._flush()

    def _flush(self) -> None:
        """Freezes MemTable, sorts keys, and pushes a new SSTable segment."""
        if not self.memtable:
            return
            
        self._segment_counter += 1
        sorted_entries = sorted(self.memtable.items(), key=lambda item: item[0])
        segment = SSTableSegment(self._segment_counter, sorted_entries)
        
        # Prepend new segment: search traverses newest -> oldest
        self.segments.insert(0, segment)
        self.memtable.clear()
        print(f"  [FLUSH] MemTable flushed to SSTable Segment #{segment.segment_id} ({len(sorted_entries)} records)")

    def get(self, key: str) -> Optional[str]:
        """Retrieves value for key by querying MemTable first, then scanning SSTables."""
        # 1. Check in-memory MemTable first (most recent state)
        if key in self.memtable:
            val = self.memtable[key]
            return val  # Returns None if deleted tombstone is present

        # 2. Search SSTable segments from newest to oldest
        for segment in self.segments:
            found, val = segment.get(key)
            if found:
                return val  # If tombstone (None), key is deleted

        return None


if __name__ == "__main__":
    print("--- Initializing Log-Structured Merge-Tree Engine ---\n")

    # Initialize LSM-Tree with small flush threshold to observe segment transitions
    db = LSMTree(memtable_threshold=3)

    print("[PHASE 1: Writes & Automated Segment Flushing]")
    db.put("user:101", "Alice")
    db.put("user:102", "Bob")
    db.put("user:103", "Charlie")  # Triggers Flush #1 (Segment 1)

    db.put("user:104", "Dave")
    db.put("user:101", "Alice_Updated")  # Overwrite Alice
    db.put("user:105", "Eve")      # Triggers Flush #2 (Segment 2)

    db.put("user:106", "Frank")
    db.delete("user:102")          # Tombstone write for Bob

    print("\n[ENGINE STATUS]")
    print(f"  MemTable Entries (Active RAM) : {len(db.memtable)}")
    print(f"  SSTable Segments (Flushed)    : {len(db.segments)}")
    print("-" * 65)

    print("\n[PHASE 2: Point Lookups Across MemTable & SSTables]")
    queries = ["user:101", "user:102", "user:103", "user:106", "user:999"]
    for q in queries:
        res = db.get(q)
        status = f"FOUND ('{res}')" if res is not None else "NOT FOUND / DELETED"
        print(f"  Lookup '{q:<8}' ---> {status}")

# Output :
# --- Initializing Log-Structured Merge-Tree Engine ---

# [PHASE 1: Writes & Automated Segment Flushing]
#   [FLUSH] MemTable flushed to SSTable Segment #1 (3 records)
#   [FLUSH] MemTable flushed to SSTable Segment #2 (3 records)

# [ENGINE STATUS]
#   MemTable Entries (Active RAM) : 2
#   SSTable Segments (Flushed)    : 2
# -----------------------------------------------------------------

# [PHASE 2: Point Lookups Across MemTable & SSTables]
#   Lookup 'user:101' ---> FOUND ('Alice_Updated')
#   Lookup 'user:102' ---> NOT FOUND / DELETED
#   Lookup 'user:103' ---> FOUND ('Charlie')
#   Lookup 'user:106' ---> FOUND ('Frank')
#   Lookup 'user:999' ---> NOT FOUND / DELETED
