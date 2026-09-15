from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class Ordering(Enum):
    EQUAL = auto()
    BEFORE = auto()      # Self happened strictly before Other (Self -> Other)
    AFTER = auto()       # Self happened strictly after Other (Other -> Self)
    CONCURRENT = auto()  # Conflict detected! Neither causally precedes the other (Self || Other)


class VectorClock:
    """Logical vector clock tracking causality across distributed nodes."""

    def __init__(self, clock_dict: Optional[Dict[str, int]] = None):
        # Maps node_id -> logical_counter
        self.clock: Dict[str, int] = dict(clock_dict) if clock_dict else {}

    def increment(self, node_id: str) -> None:
        """Increments the local counter for a given node event."""
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock') -> 'VectorClock':
        """Merges two vector clocks by taking the component-wise maximum."""
        merged_keys = set(self.clock.keys()).union(other.clock.keys())
        merged_dict = {
            k: max(self.clock.get(k, 0), other.clock.get(k, 0))
            for k in merged_keys
        }
        return VectorClock(merged_dict)

    def compare(self, other: 'VectorClock') -> Ordering:
        """Determines partial causal ordering between self and another vector clock."""
        all_keys = set(self.clock.keys()).union(other.clock.keys())

        self_has_greater = False
        other_has_greater = False

        for k in all_keys:
            v_self = self.clock.get(k, 0)
            v_other = other.clock.get(k, 0)

            if v_self > v_other:
                self_has_greater = True
            elif v_other > v_self:
                other_has_greater = True

        if not self_has_greater and not other_has_greater:
            return Ordering.EQUAL
        elif self_has_greater and not other_has_greater:
            return Ordering.AFTER   # self strictly dominated other
        elif other_has_greater and not self_has_greater:
            return Ordering.BEFORE  # other strictly dominated self
        else:
            return Ordering.CONCURRENT  # Both have strictly greater elements -> Conflict!

    def __str__(self) -> str:
        sorted_items = sorted(self.clock.items())
        return "{" + ", ".join(f"'{k}': {v}" for k, v in sorted_items) + "}"


@dataclass
class VersionedValue:
    value: str
    vector_clock: VectorClock


class CausallyConsistentStore:
    """A distributed key-value node using vector clocks for causal conflict detection."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        # Key -> List of concurrent values (siblings/branches)
        self.store: Dict[str, List[VersionedValue]] = {}

    def put(self, key: str, value: str, context_clock: Optional[VectorClock] = None) -> VectorClock:
        """Writes a value. Uses client context_clock or existing key clock to update state."""
        if context_clock is None:
            # New key write
            new_clock = VectorClock()
        else:
            new_clock = VectorClock(context_clock.clock)

        new_clock.increment(self.node_id)
        new_version = VersionedValue(value=value, vector_clock=new_clock)

        if key not in self.store:
            self.store[key] = [new_version]
        else:
            # Filter out older versions strictly dominated by new_clock
            remaining_versions: List[VersionedValue] = []
            for existing in self.store[key]:
                relation = new_clock.compare(existing.vector_clock)
                if relation == Ordering.CONCURRENT:
                    remaining_versions.append(existing)
                # If relation is AFTER, existing version is obsolete and replaced

            remaining_versions.append(new_version)
            self.store[key] = remaining_versions

        print(f"  [Node {self.node_id} WRITE] Key='{key}', Val='{value}', Clock={new_clock}")
        return new_clock

    def get(self, key: str) -> Tuple[List[str], Optional[VectorClock]]:
        """Returns all concurrent values (siblings) and merged vector clock context."""
        if key not in self.store or not self.store[key]:
            return [], None

        versions = self.store[key]
        values = [v.value for v in versions]

        # Combine vector clocks into a single read-context vector clock
        merged_clock = versions[0].vector_clock
        for v in versions[1:]:
            merged_clock = merged_clock.merge(v.vector_clock)

        if len(versions) > 1:
            print(f"  [Node {self.node_id} READ CONFLICT DETECTED!] Key='{key}' has {len(versions)} concurrent branches: {values}")
        else:
            print(f"  [Node {self.node_id} READ] Key='{key}', Val='{values[0]}', Clock={merged_clock}")

        return values, merged_clock


# --- Distributed Causality Simulation ---

if __name__ == "__main__":
    print("--- Initializing Vector Clock Causal Consistency Engine ---\n")

    # Nodes in a multi-datacenter replica set
    node_a = CausallyConsistentStore(node_id="NodeA")
    node_b = CausallyConsistentStore(node_id="NodeB")

    print("[STEP 1: Sequential Sequential Writes (Causal Precedence)]")
    # Client writes key 'title' to Node A
    clock1 = node_a.put(key="item_title", value="Initial Title", context_clock=None)

    # Client reads from Node A, then updates on Node B (Causally depends on clock1)
    clock2 = node_b.put(key="item_title", value="Title Updated by User B", context_clock=clock1)
    print("-" * 65)

    print("\n[STEP 2: Concurrent Divergent Writes (Network Partition / Branching)]")
    # Concurrent write 1: Client 1 updates based on original clock1 on Node A
    clock_a = node_a.put(key="item_title", value="Title Edit from Client 1", context_clock=clock1)

    # Concurrent write 2: Client 2 updates based on original clock1 on Node B
    clock_b = node_b.put(key="item_title", value="Title Edit from Client 2", context_clock=clock1)

    print("\n[STEP 3: Vector Clock Comparison for Concurrent Branches]")
    relation = clock_a.compare(clock_b)
    print(f"  Clock A: {clock_a}")
    print(f"  Clock B: {clock_b}")
    print(f"  Causal Relationship: {relation.name} (Neither clock dominates -> Conflict!)")
    print("-" * 65)

    print("\n[STEP 4: Replica Synchronization & Conflict Detection on Read]")
    # Replicate Node B's state into Node A
    node_a.store["item_title"].extend(node_b.store["item_title"])

    # Client reads from Node A and discovers siblings
    siblings, read_context = node_a.get(key="item_title")

    print("\n[STEP 5: Conflict Resolution (Sibling Merging)]")
    # Application merges siblings and writes back merged state with read_context
    merged_val = " & ".join(siblings)
    final_clock = node_a.put(key="item_title", value=f"Merged[{merged_val}]", context_clock=read_context)

    # Re-read to verify single resolved state
    node_a.get(key="item_title")
    print("-" * 65)
    print("[SUCCESS] Causal ordering maintained and concurrent writes safely reconciled!")

# Output :
# --- Initializing Vector Clock Causal Consistency Engine ---

# [STEP 1: Sequential Sequential Writes (Causal Precedence)]
#   [Node NodeA WRITE] Key='item_title', Val='Initial Title', Clock={'NodeA': 1}
#   [Node NodeB WRITE] Key='item_title', Val='Title Updated by User B', Clock={'NodeA': 1, 'NodeB': 1}
# -----------------------------------------------------------------

# [STEP 2: Concurrent Divergent Writes (Network Partition / Branching)]
#   [Node NodeA WRITE] Key='item_title', Val='Title Edit from Client 1', Clock={'NodeA': 2}
#   [Node NodeB WRITE] Key='item_title', Val='Title Edit from Client 2', Clock={'NodeA': 1, 'NodeB': 1}

# [STEP 3: Vector Clock Comparison for Concurrent Branches]
#   Clock A: {'NodeA': 2}
#   Clock B: {'NodeA': 1, 'NodeB': 1}
#   Causal Relationship: CONCURRENT (Neither clock dominates -> Conflict!)
# -----------------------------------------------------------------

# [STEP 4: Replica Synchronization & Conflict Detection on Read]
#   [Node NodeA READ CONFLICT DETECTED!] Key='item_title' has 2 concurrent branches: ['Title Edit from Client 1', 'Title Edit from Client 2']

# [STEP 5: Conflict Resolution (Sibling Merging)]
#   [Node NodeA WRITE] Key='item_title', Val='Merged[Title Edit from Client 1 & Title Edit from Client 2]', Clock={'NodeA': 3, 'NodeB': 1}
#   [Node NodeA READ] Key='item_title', Val='Merged[Title Edit from Client 1 & Title Edit from Client 2]', Clock={'NodeA': 3, 'NodeB': 1}
# -----------------------------------------------------------------
# [SUCCESS] Causal ordering maintained and concurrent writes safely reconciled!
