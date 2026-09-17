import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


class PNCounter:
    """State-based Conflict-Free Replicated PN-Counter (Positive-Negative Counter)."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        # Vector of increments (P-Vector) and decrements (N-Vector)
        self.p_vector: Dict[str, int] = {}
        self.n_vector: Dict[str, int] = {}

    def increment(self, value: int = 1) -> None:
        """Increments node counter."""
        self.p_vector[self.node_id] = self.p_vector.get(self.node_id, 0) + value

    def decrement(self, value: int = 1) -> None:
        """Decrements node counter."""
        self.n_vector[self.node_id] = self.n_vector.get(self.node_id, 0) + value

    def read(self) -> int:
        """Computes current value = sum(P) - sum(N)."""
        return sum(self.p_vector.values()) - sum(self.n_vector.values())

    def merge(self, other: 'PNCounter') -> 'PNCounter':
        """Join operator (LUB): Component-wise max across P and N vectors."""
        merged = PNCounter(self.node_id)
        
        all_p_keys = set(self.p_vector.keys()).union(other.p_vector.keys())
        all_n_keys = set(self.n_vector.keys()).union(other.n_vector.keys())

        merged.p_vector = {k: max(self.p_vector.get(k, 0), other.p_vector.get(k, 0)) for k in all_p_keys}
        merged.n_vector = {k: max(self.n_vector.get(k, 0), other.n_vector.get(k, 0)) for k in all_n_keys}
        
        return merged


@dataclass(frozen=True)
class TaggedElement:
    element: Any
    tag: str  # Unique UUID tag generated on insertion


class ORSet:
    """State-based Observed-Remove Set (Add-wins semantics over concurrent deletes)."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        # Add set (E) and Remove set (R) of TaggedElements
        self.add_set: Set[TaggedElement] = set()
        self.remove_set: Set[TaggedElement] = set()

    def add(self, element: Any) -> TaggedElement:
        """Adds element with a unique tag."""
        tagged = TaggedElement(element=element, tag=str(uuid.uuid4()))
        self.add_set.add(tagged)
        return tagged

    def remove(self, element: Any) -> None:
        """Removes all currently observed instances of element by copying their tags into remove_set."""
        observed_tags = {item for item in self.add_set if item.element == element}
        self.remove_set.update(observed_tags)

    def read(self) -> Set[Any]:
        """Returns active elements = {e | tag in AddSet AND tag NOT in RemoveSet}."""
        active_tagged = self.add_set - self.remove_set
        return {item.element for item in active_tagged}

    def merge(self, other: 'ORSet') -> 'ORSet':
        """Join operator (LUB): Set union for both AddSet and RemoveSet."""
        merged = ORSet(self.node_id)
        merged.add_set = self.add_set.union(other.add_set)
        merged.remove_set = self.remove_set.union(other.remove_set)
        return merged


# --- Asynchronous Replication Simulation ---

if __name__ == "__main__":
    print("--- Initializing State-Based CRDT Engine (PN-Counter & OR-Set) ---\n")

    # -------------------------------------------------------------
    # 1. PN-COUNTER TEST
    # -------------------------------------------------------------
    print("[1. PN-COUNTER: Concurrent Counter Operations]")
    node_a_cnt = PNCounter("NodeA")
    node_b_cnt = PNCounter("NodeB")

    # Concurrent operations
    node_a_cnt.increment(5)
    node_a_cnt.decrement(2)

    node_b_cnt.increment(10)
    node_b_cnt.decrement(1)

    print(f"  Node A local count: {node_a_cnt.read()}")
    print(f"  Node B local count: {node_b_cnt.read()}")

    # Merge states out-of-order
    merged_a = node_a_cnt.merge(node_b_cnt)
    merged_b = node_b_cnt.merge(node_a_cnt)

    print(f"  After Merge (Node A view): {merged_a.read()}")
    print(f"  After Merge (Node B view): {merged_b.read()}")
    assert merged_a.read() == merged_b.read() == 12
    print("  -> Converged! (5 - 2 + 10 - 1 = 12)\n")

    # -------------------------------------------------------------
    # 2. OR-SET TEST (Add-Wins Semantics)
    # -------------------------------------------------------------
    print("[2. OR-SET: Concurrent Add / Remove Disambiguation]")
    node_a_set = ORSet("NodeA")
    node_b_set = ORSet("NodeB")

    # Initial state sync: Both nodes know 'item_x' exists
    item_tag = node_a_set.add("item_x")
    node_b_set = node_b_set.merge(node_a_set)

    print(f"  Initial Sync State: Node A={node_a_set.read()} | Node B={node_b_set.read()}")

    # Concurrent Partition Writes:
    # Node A removes 'item_x' (observes existing tag)
    node_a_set.remove("item_x")

    # Node B re-adds 'item_x' concurrently (generates NEW tag)
    node_b_set.add("item_x")

    print(f"  Node A (Partitioned): {node_a_set.read()}")
    print(f"  Node B (Partitioned): {node_b_set.read()}")

    # Merge divergent partitions
    final_a = node_a_set.merge(node_b_set)
    final_b = node_b_set.merge(node_a_set)

    print("\n  [MERGING DIVERGENT STATES]")
    print(f"  Merged Set View (Node A): {final_a.read()}")
    print(f"  Merged Set View (Node B): {final_b.read()}")

    assert final_a.read() == final_b.read() == {"item_x"}
    print("-" * 65)
    print("[SUCCESS] Add-Wins semantics preserved! Convergence achieved across out-of-order operations.")
