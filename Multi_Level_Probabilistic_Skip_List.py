import random
from typing import Optional, List, Tuple

class SkipListNode:
    """A node inside the multi-level Skip List."""
    def __init__(self, key: int, value: str, level: int):
        self.key = key
        self.value = value
        # Forward pointers array for each level this node participates in
        self.forward: List[Optional['SkipListNode']] = [None] * (level + 1)

    def __repr__(self) -> str:
        return f"Node({self.key}: '{self.value}')"


class SkipList:
    """A Probabilistic Skip List supporting O(log N) search, insertion, and range queries."""
    
    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p  # Probability of promotion to next level (typically 0.5 or 0.25)
        self.level = 0  # Current maximum level active in the list
        
        # Sentinel head node initialized with maximum level capacity
        self.head = SkipListNode(key=float('-inf'), value="__HEAD__", level=max_level)

    def _random_level(self) -> int:
        """Simulates geometric coin tosses to assign a node's tower height."""
        lvl = 0
        while random.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def search(self, key: int) -> Optional[str]:
        """Searches for a key across skip levels in O(log N) time."""
        current = self.head
        
        # Traverse top-down from highest active level to level 0
        for lvl in range(self.level, -1, -1):
            while current.forward[lvl] and current.forward[lvl].key < key:
                current = current.forward[lvl]

        # Drop down to level 0 and step to the candidate node
        candidate = current.forward[0]
        if candidate and candidate.key == key:
            return candidate.value
        return None

    def insert(self, key: int, value: str) -> None:
        """Inserts or updates a key-value pair, splicing forward pointers across levels."""
        update = [None] * (self.max_level + 1)
        current = self.head

        # Step 1: Record update predecessors at each level
        for lvl in range(self.level, -1, -1):
            while current.forward[lvl] and current.forward[lvl].key < key:
                current = current.forward[lvl]
            update[lvl] = current

        candidate = current.forward[0]

        # Update existing key in-place
        if candidate and candidate.key == key:
            candidate.value = value
            return

        # Step 2: Generate random level tower for new node
        new_level = self._random_level()

        # If new node exceeds current skip list height, initialize head links
        if new_level > self.level:
            for lvl in range(self.level + 1, new_level + 1):
                update[lvl] = self.head
            self.level = new_level

        # Step 3: Instantiate node and splice pointers into levels
        new_node = SkipListNode(key, value, new_level)
        for lvl in range(new_level + 1):
            new_node.forward[lvl] = update[lvl].forward[lvl]
            update[lvl].forward[lvl] = new_node

    def delete(self, key: int) -> bool:
        """Removes a key from all levels in O(log N) time."""
        update = [None] * (self.max_level + 1)
        current = self.head

        for lvl in range(self.level, -1, -1):
            while current.forward[lvl] and current.forward[lvl].key < key:
                current = current.forward[lvl]
            update[lvl] = current

        candidate = current.forward[0]
        if not candidate or candidate.key != key:
            return False

        # Unlink candidate node from all levels it participates in
        for lvl in range(self.level + 1):
            if update[lvl].forward[lvl] != candidate:
                break
            update[lvl].forward[lvl] = candidate.forward[lvl]

        # Adjust list's top level if highest level became empty
        while self.level > 0 and self.head.forward[self.level] is None:
            self.level -= 1

        return True

    def range_query(self, min_key: int, max_key: int) -> List[Tuple[int, str]]:
        """Performs an ordered range scan from min_key to max_key inclusive."""
        results = []
        current = self.head

        # Locate first element >= min_key via fast skip navigation
        for lvl in range(self.level, -1, -1):
            while current.forward[lvl] and current.forward[lvl].key < min_key:
                current = current.forward[lvl]

        current = current.forward[0]

        # Scan horizontally along level 0
        while current and current.key <= max_key:
            results.append((current.key, current.value))
            current = current.forward[0]

        return results


if __name__ == "__main__":
    print("--- Initializing Multi-Level Probabilistic Skip List ---\n")

    skip_list = SkipList(max_level=8, p=0.5)

    # 1. Insert structured records
    dataset = [
        (25, "Metric_Alpha"),
        (10, "Metric_Beta"),
        (40, "Metric_Gamma"),
        (5,  "Metric_Delta"),
        (18, "Metric_Epsilon"),
        (32, "Metric_Zeta"),
        (50, "Metric_Eta")
    ]

    print("[INSERTION] Ingesting keys into Skip List...")
    for key, val in dataset:
        skip_list.insert(key, val)

    print(f"  Max Level Reached: Level {skip_list.level}")
    print("-" * 65)

    # 2. Point Query Lookups
    print("\n[POINT LOOKUPS]")
    for test_key in [18, 40, 99]:
        res = skip_list.search(test_key)
        status = f"FOUND ('{res}')" if res else "NOT FOUND"
        print(f"  Key {test_key:>2} ---> {status}")

    # 3. Ordered Range Scan along Level 0
    print("\n[RANGE SCAN] Querying records between keys 10 and 40:")
    records = skip_list.range_query(10, 40)
    for k, v in records:
        print(f"  Record -> Key: {k:>2} | Value: '{v}'")

    # 4. Deletion
    print("\n[DELETION] Removing Key 18...")
    deleted = skip_list.delete(18)
    print(f"  Deleted: {deleted} | Search Key 18 Post-Delete: {skip_list.search(18)}")

# Output :
# --- Initializing Multi-Level Probabilistic Skip List ---

# [INSERTION] Ingesting keys into Skip List...
#   Max Level Reached: Level 3
# -----------------------------------------------------------------

# [POINT LOOKUPS]
#   Key 18 ---> FOUND ('Metric_Epsilon')
#   Key 40 ---> FOUND ('Metric_Gamma')
#   Key 99 ---> NOT FOUND

# [RANGE SCAN] Querying records between keys 10 and 40:
#   Record -> Key: 10 | Value: 'Metric_Beta'
#   Record -> Key: 18 | Value: 'Metric_Epsilon'
#   Record -> Key: 25 | Value: 'Metric_Alpha'
#   Record -> Key: 32 | Value: 'Metric_Zeta'
#   Record -> Key: 40 | Value: 'Metric_Gamma'

# [DELETION] Removing Key 18...
#   Deleted: True | Search Key 18 Post-Delete: None
