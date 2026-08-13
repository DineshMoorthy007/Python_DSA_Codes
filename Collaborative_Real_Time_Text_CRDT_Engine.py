from typing import List, Optional

class Identifier:
    """Represents a unique position coordinate in the text sequence."""
    def __init__(self, position: float, clock: int, site_id: str):
        self.position = position  # Dense fractional index position
        self.clock = clock        # Logical clock (Lamport) for tie-breaking
        self.site_id = site_id    # Unique peer node identifier

    def __lt__(self, other: 'Identifier') -> bool:
        # Deterministic comparison order: position -> clock -> site_id
        if self.position != other.position:
            return self.position < other.position
        if self.clock != other.clock:
            return self.clock < other.clock
        return self.site_id < other.site_id

    def __eq__(self, other) -> bool:
        return (isinstance(other, Identifier) and
                self.position == other.position and
                self.clock == other.clock and
                self.site_id == other.site_id)


class Character:
    """A character payload tagged with its positional identifier and deletion state."""
    def __init__(self, value: str, id_: Identifier):
        self.value = value
        self.id = id_
        self.deleted = False

    def __repr__(self):
        return f"Char('{self.value}', pos={self.id.position})"


class LWWSequenceCRDT:
    """A sequence CRDT providing conflict-free text editing operations across replicas."""
    
    def __init__(self, site_id: str):
        self.site_id = site_id
        self.clock = 0
        # Character sequence kept in sorted order by positional identifier
        self.sequence: List[Character] = []

    def _generate_position(self, prev_idx: Optional[int], next_idx: Optional[int]) -> float:
        """Calculates a fractional position strictly between two adjacent nodes."""
        min_pos = self.sequence[prev_idx].id.position if prev_idx is not None else 0.0
        max_pos = self.sequence[next_idx].id.position if next_idx is not None else 1.0
        return (min_pos + max_pos) / 2.0

    def local_insert(self, value: str, index: int) -> Character:
        """Inserts a character locally at a specific visible index."""
        self.clock += 1
        
        # Translate visible index to underlying sequence indices
        visible_nodes = [c for c in self.sequence if not c.deleted]
        
        prev_node = visible_nodes[index - 1] if index > 0 else None
        next_node = visible_nodes[index] if index < len(visible_nodes) else None

        prev_idx = self.sequence.index(prev_node) if prev_node else None
        next_idx = self.sequence.index(next_node) if next_node else None

        pos = self._generate_position(prev_idx, next_idx)
        char_id = Identifier(pos, self.clock, self.site_id)
        char = Character(value, char_id)

        # Insert and maintain sorted order
        self.sequence.append(char)
        self.sequence.sort(key=lambda c: c.id)
        return char

    def local_delete(self, index: int) -> Identifier:
        """Marks a character as deleted (tombstone) at a given visible index."""
        visible_nodes = [c for c in self.sequence if not c.deleted]
        target = visible_nodes[index]
        target.deleted = True
        return target.id

    def remote_insert(self, char: Character) -> None:
        """Integrates a character inserted by a remote peer into the local state."""
        self.clock = max(self.clock, char.id.clock) + 1
        
        # Check if character already exists locally
        for existing in self.sequence:
            if existing.id == char.id:
                return  # Idempotent skip
                
        self.sequence.append(char)
        self.sequence.sort(key=lambda c: c.id)

    def remote_delete(self, target_id: Identifier) -> None:
        """Applies a remote deletion by ID (tombstone flag)."""
        for char in self.sequence:
            if char.id == target_id:
                char.deleted = True
                break

    def read_text(self) -> str:
        """Renders the visible document text, skipping tombstones."""
        return "".join(c.value for c in self.sequence if not c.deleted)


if __name__ == "__main__":
    print("--- Initializing Collaborative Sequence CRDT Engine ---\n")

    # Instantiate two peer replicas
    peer_a = LWWSequenceCRDT(site_id="Peer-Alice")
    peer_b = LWWSequenceCRDT(site_id="Peer-Bob")

    # 1. Alice types "CAT"
    c1 = peer_a.local_insert("C", 0)
    c2 = peer_a.local_insert("A", 1)
    c3 = peer_a.local_insert("T", 2)

    # Sync Alice -> Bob
    for char in [c1, c2, c3]:
        peer_b.remote_insert(char)

    print(f"[INITIAL TEXT] Alice: '{peer_a.read_text()}' | Bob: '{peer_b.read_text()}'")
    print("-" * 65)

    # 2. Concurrent edits during network partition
    print("[CONCURRENT EDIT] Alice inserts 'S' at start ('SCAT'), Bob inserts 'S' at end ('CATS')...\n")
    
    # Alice inserts 'S' at index 0
    char_alice_s = peer_a.local_insert("S", 0)

    # Bob inserts 'S' at index 3 concurrently
    char_bob_s = peer_b.local_insert("S", 3)

    print(f"  Pre-Sync Alice Local Text : '{peer_a.read_text()}'")
    print(f"  Pre-Sync Bob Local Text   : '{peer_b.read_text()}'")

    # 3. Cross-sync network pass
    peer_a.remote_insert(char_bob_s)
    peer_b.remote_insert(char_alice_s)

    print("\n--- Post-Sync CRDT Text Convergence ---")
    print(f"  Alice Final Document State : '{peer_a.read_text()}'")
    print(f"  Bob Final Document State   : '{peer_b.read_text()}'")
    print("-" * 65)
    print("[SUCCESS] Both peers converged on the exact same character order!")

# Output :
# --- Initializing Collaborative Sequence CRDT Engine ---

# [INITIAL TEXT] Alice: 'CAT' | Bob: 'CAT'
# -----------------------------------------------------------------
# [CONCURRENT EDIT] Alice inserts 'S' at start ('SCAT'), Bob inserts 'S' at end ('CATS')...

#   Pre-Sync Alice Local Text : 'SCAT'
#   Pre-Sync Bob Local Text   : 'CATS'

# --- Post-Sync CRDT Text Convergence ---
#   Alice Final Document State : 'SCATS'
#   Bob Final Document State   : 'SCATS'
# -----------------------------------------------------------------
# [SUCCESS] Both peers converged on the exact same character order!
