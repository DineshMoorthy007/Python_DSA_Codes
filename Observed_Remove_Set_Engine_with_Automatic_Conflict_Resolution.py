import uuid
from typing import Generic, TypeVar, Set, Tuple

T = TypeVar('T')

class ElementTag(Generic[T]):
    """Represents a unique instance tag for an added element."""
    def __init__(self, value: T, tag_id: str = None):
        self.value = value
        self.tag_id = tag_id or str(uuid.uuid4())

    def __eq__(self, other):
        return isinstance(other, ElementTag) and self.tag_id == other.tag_id

    def __hash__(self):
        return hash(self.tag_id)


class ORSet(Generic[T]):
    """An Observed-Remove Set (OR-Set) State-Based CRDT.
    
    Guarantees strong eventual consistency across decoupled nodes.
    Additions take precedence over concurrent deletions (Add-Wins policy).
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        # Add Set: Tracks active (element, unique_tag) pairs
        self.add_set: Set[Tuple[T, str]] = set()
        # Remove Set (Tombstones): Tracks observed and deleted (element, unique_tag) pairs
        self.remove_set: Set[Tuple[T, str]] = set()

    def add(self, element: T) -> str:
        """Adds an element by assigning a globally unique UUID tag.
        
        Returns the unique tag generated for this insertion.
        """
        tag_id = str(uuid.uuid4())
        self.add_set.add((element, tag_id))
        return tag_id

    def remove(self, element: T) -> None:
        """Removes an element by moving all currently observed tags into the tombstone set."""
        # Find all active tags for this element currently visible to this node
        observed_tags = {pair for pair in self.add_set if pair[0] == element}
        # Add all observed tags to the remove set (tombstone set)
        self.remove_set.update(observed_tags)

    def read(self) -> Set[T]:
        """Returns the current state of the set (Add Set minus Tombstone Set)."""
        active_pairs = self.add_set - self.remove_set
        return {element for element, _ in active_pairs}

    def merge(self, remote_or_set: 'ORSet[T]') -> None:
        """Merges a remote node's OR-Set state into the local state.
        
        Uses commutative, associative, and idempotent union operations.
        """
        self.add_set.update(remote_or_set.add_set)
        self.remove_set.update(remote_or_set.remove_set)


if __name__ == "__main__":
    print("--- Initializing Decentralized OR-Set (Add-Wins) Engine ---\n")

    # Instantiate two disconnected replica nodes
    node_a = ORSet[str]("Node-Alpha")
    node_b = ORSet[str]("Node-Beta")

    # 1. Initial State: Node A adds items and syncs with Node B
    node_a.add("Document_1.pdf")
    node_a.add("Image_2.png")
    
    # Sync Node A -> Node B
    node_b.merge(node_a)

    print("[INITIAL SYNC] Both nodes hold identical initial state:")
    print(f"  Node Alpha Read : {node_a.read()}")
    print(f"  Node Beta Read  : {node_b.read()}")

    print("-" * 65)
    print("[CONCURRENT MUTATION] Simulating a network split between Node Alpha and Node Beta...\n")

    # Node Alpha DELETES "Document_1.pdf" (Observes and removes pre-existing tags)
    node_a.remove("Document_1.pdf")
    print("  [Node Alpha] Deleted 'Document_1.pdf'")

    # Concurrent Action: Node Beta RE-ADDS "Document_1.pdf" (Generates a brand new unique tag!)
    node_b.add("Document_1.pdf")
    print("  [Node Beta]  Re-added 'Document_1.pdf' concurrently")

    print("\n--- Pre-Sync Divergent Local Views ---")
    print(f"  Node Alpha Local View : {node_a.read()}")
    print(f"  Node Beta Local View  : {node_b.read()}")

    # 2. Perform Bi-Directional Cross-Sync over the network
    node_a.merge(node_b)
    node_b.merge(node_a)

    print("\n--- Post-Sync CRDT Convergence (Add-Wins Resolution) ---")
    print(f"  Node Alpha Final State : {node_a.read()}")
    print(f"  Node Beta Final State  : {node_b.read()}")
    print("-" * 65)
    print("[SUCCESS] Both nodes converged to the exact same state without locks or central consensus!")

# Output :
# --- Initializing Decentralized OR-Set (Add-Wins) Engine ---

# [INITIAL SYNC] Both nodes hold identical initial state:
#   Node Alpha Read : {'Document_1.pdf', 'Image_2.png'}
#   Node Beta Read  : {'Document_1.pdf', 'Image_2.png'}
# -----------------------------------------------------------------
# [CONCURRENT MUTATION] Simulating a network split between Node Alpha and Node Beta...

#   [Node Alpha] Deleted 'Document_1.pdf'
#   [Node Beta]  Re-added 'Document_1.pdf' concurrently

# --- Pre-Sync Divergent Local Views ---
#   Node Alpha Local View : {'Image_2.png'}
#   Node Beta Local View  : {'Document_1.pdf', 'Image_2.png'}

# --- Post-Sync CRDT Convergence (Add-Wins Resolution) ---
#   Node Alpha Final State : {'Document_1.pdf', 'Image_2.png'}
#   Node Beta Final State  : {'Document_1.pdf', 'Image_2.png'}
# -----------------------------------------------------------------
# [SUCCESS] Both nodes converged to the exact same state without locks or central consensus!
