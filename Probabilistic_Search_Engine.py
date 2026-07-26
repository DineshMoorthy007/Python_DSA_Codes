import random

class SkipNode:
    """A single node storing a value and dynamic forward-pointers across levels."""
    def __init__(self, val: int, level: int):
        self.val = val
        # Array of pointers to next nodes at each level (0 through level - 1)
        self.forward: list[SkipNode | None] = [None] * level


class SkipList:
    """A probabilistic data structure achieving logarithmic lookups and inserts."""
    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p
        # Current highest active level in the list
        self.level = 1
        # Sentinel head node initialized with minimum integer baseline
        self.head = SkipNode(-1, self.max_level)

    def _random_level(self) -> int:
        """Flips a coin to randomly assign a level height for new nodes."""
        lvl = 1
        while random.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def search(self, target: int) -> bool:
        """Searches for a target value in logarithmic O(log n) time."""
        current = self.head

        # Start from the top speed-lane level and walk down
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].val < target:
                current = current.forward[i]

        # Move to the bottom-most level neighbor
        current = current.forward[0]
        return current is not None and current.val == target

    def insert(self, num: int) -> None:
        """Inserts a new value into the hierarchy."""
        update = [None] * self.max_level
        current = self.head

        # Traversal pass: Record predecessor pointers for every level
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].val < num:
                current = current.forward[i]
            update[i] = current

        # Generate a random height tier for the new node
        new_level = self._random_level()

        # If the new level exceeds our current maximum level, adjust head tracking
        if new_level > self.level:
            for i in range(self.level, new_level):
                update[i] = self.head
            self.level = new_level

        # Allocate new node and update forward pointers across assigned levels
        new_node = SkipNode(num, new_level)
        for i in range(new_level):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node

    def erase(self, num: int) -> bool:
        """Removes a value and updates pointer bridges across affected levels."""
        update = [None] * self.max_level
        current = self.head

        # Traversal pass: Locate predecessor pointers
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].val < num:
                current = current.forward[i]
            update[i] = current

        target_node = current.forward[0]

        # Target node missing
        if not target_node or target_node.val != num:
            return False

        # Unlink target node pointers across all active level tiers
        for i in range(self.level):
            if update[i].forward[i] != target_node:
                break
            update[i].forward[i] = target_node.forward[i]

        # Recalculate max active level if top tiers become empty
        while self.level > 1 and self.head.forward[self.level - 1] is None:
            self.level -= 1

        return True


if __name__ == "__main__":
    print("--- Initializing Multi-Level Skip List Engine ---")
    
    skiplist = SkipList()

    # Ingest numerical values
    data_stream = [30, 10, 50, 20, 40]
    print(f"Ingesting stream: {data_stream}")
    for value in data_stream:
        skiplist.insert(value)

    print("-" * 55)
    print(f"Lookup Search: '20' present? -> {skiplist.search(20)}")
    print(f"Lookup Search: '90' present? -> {skiplist.search(90)}")

    print("\n[ERASE OPERATION] Deleting value '20'...")
    skiplist.erase(20)
    print(f"Lookup Search: '20' present post-deletion? -> {skiplist.search(20)}")

# Output :
# --- Initializing Multi-Level Skip List Engine ---
# Ingesting stream: [30, 10, 50, 20, 40]
# -------------------------------------------------------
# Lookup Search: '20' present? -> True
# Lookup Search: '90' present? -> False

# [ERASE OPERATION] Deleting value '20'...
# Lookup Search: '20' present post-deletion? -> False
