from enum import Enum, auto
from typing import Dict, Any

class Causality(Enum):
    BEFORE = auto()      # Event A causally preceded Event B
    AFTER = auto()       # Event A causally succeeded Event B
    EQUAL = auto()       # Event A and Event B are identical
    CONCURRENT = auto()  # Event A and Event B occurred concurrently (Conflict!)


class VectorClock:
    """Tracks causal dependencies across distributed nodes using logical clock vectors."""

    def __init__(self, clock_dict: Dict[str, int] = None):
        self.clock: Dict[str, int] = clock_dict.copy() if clock_dict else {}

    def increment(self, node_id: str) -> None:
        """Increments the local clock counter for a specific node."""
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def update(self, remote_clock: 'VectorClock') -> None:
        """Merges a remote vector clock by taking the element-wise maximum."""
        all_nodes = set(self.clock.keys()).union(set(remote_clock.clock.keys()))
        for node_id in all_nodes:
            self.clock[node_id] = max(
                self.clock.get(node_id, 0),
                remote_clock.clock.get(node_id, 0)
            )

    def compare(self, other: 'VectorClock') -> Causality:
        """Compares two Vector Clocks to establish their causal relationship."""
        self_greater_or_equal = True
        other_greater_or_equal = True

        all_nodes = set(self.clock.keys()).union(set(other.clock.keys()))

        for node_id in all_nodes:
            v1 = self.clock.get(node_id, 0)
            v2 = other.clock.get(node_id, 0)

            if v1 < v2:
                self_greater_or_equal = False
            if v2 < v1:
                other_greater_or_equal = False

        if self_greater_or_equal and other_greater_or_equal:
            return Causality.EQUAL
        elif self_greater_or_equal and not other_greater_or_equal:
            return Causality.AFTER
        elif not self_greater_or_equal and other_greater_or_equal:
            return Causality.BEFORE
        else:
            return Causality.CONCURRENT

    def copy(self) -> 'VectorClock':
        return VectorClock(self.clock)

    def __repr__(self) -> str:
        return f"VC{dict(sorted(self.clock.items()))}"


class DistributedNode:
    """Simulates a database node executing local writes and processing remote syncs."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.vector_clock = VectorClock()
        self.state: Dict[str, Any] = {}

    def local_write(self, key: str, value: Any) -> VectorClock:
        """Executes a local state write, incrementing the node's local logical clock."""
        self.vector_clock.increment(self.node_id)
        self.state[key] = value
        print(f"  [{self.node_id}] Local Write: {key}='{value}' | Updated Clock: {self.vector_clock}")
        return self.vector_clock.copy()

    def receive_sync(self, remote_node_id: str, remote_clock: VectorClock, payload: Dict[str, Any]) -> None:
        """Processes an incoming network sync and merges causal clock history."""
        # Merge remote vector clock into local clock
        self.vector_clock.update(remote_clock)
        # Advance local clock step for receiving the sync message
        self.vector_clock.increment(self.node_id)
        
        # Apply remote payload updates
        self.state.update(payload)
        print(f"  [{self.node_id}] Synced from [{remote_node_id}] | Merged Clock: {self.vector_clock}")


if __name__ == "__main__":
    print("--- Initializing Distributed Vector Clock Causal Engine ---\n")

    # Instantiate two distributed nodes
    node_a = DistributedNode("Node-A")
    node_b = DistributedNode("Node-B")

    print("[SCENARIO 1: Sequential Causal Updates]")
    clock_a1 = node_a.local_write("title", "Distributed Systems")
    
    # Node B syncs from Node A
    node_b.receive_sync(node_a.node_id, clock_a1, node_a.state)
    clock_b1 = node_b.local_write("status", "Draft")

    # Evaluate causality: clock_b1 should succeed clock_a1
    relation = clock_a1.compare(clock_b1)
    print(f"\n  Relationship (Clock A1 vs Clock B1): {relation.name}")
    print("  Explanation: Clock A1 happened strictly BEFORE Clock B1.\n")

    print("-" * 65)
    print("[SCENARIO 2: Concurrent Mutation / Split-Brain Conflict]\n")
    
    # Node A writes locally while disconnected from Node B
    clock_a2 = node_a.local_write("title", "Vector Clocks in Depth")

    # Node B writes locally at the same time without seeing Node A's update
    clock_b2 = node_b.local_write("title", "Causal Ordering Made Easy")

    # Evaluate causality: neither clock dominates the other -> CONCURRENT!
    conflict_relation = clock_a2.compare(clock_b2)
    print(f"\n  Clock A2: {clock_a2}")
    print(f"  Clock B2: {clock_b2}")
    print(f"  Relationship: {conflict_relation.name}")
    print("  [RESULT] Detected concurrent write conflict! Application intervention required.")

# Output :
# --- Initializing Distributed Vector Clock Causal Engine ---

# [SCENARIO 1: Sequential Causal Updates]
#   [Node-A] Local Write: title='Distributed Systems' | Updated Clock: VC{'Node-A': 1}
#   [Node-B] Synced from [Node-A] | Merged Clock: VC{'Node-A': 1, 'Node-B': 1}
#   [Node-B] Local Write: status='Draft' | Updated Clock: VC{'Node-A': 1, 'Node-B': 2}

#   Relationship (Clock A1 vs Clock B1): BEFORE
#   Explanation: Clock A1 happened strictly BEFORE Clock B1.

# -----------------------------------------------------------------
# [SCENARIO 2: Concurrent Mutation / Split-Brain Conflict]

#   [Node-A] Local Write: title='Vector Clocks in Depth' | Updated Clock: VC{'Node-A': 2}
#   [Node-B] Local Write: title='Causal Ordering Made Easy' | Updated Clock: VC{'Node-A': 1, 'Node-B': 3}

#   Clock A2: VC{'Node-A': 2}
#   Clock B2: VC{'Node-A': 1, 'Node-B': 3}
#   Relationship: CONCURRENT
#   [RESULT] Detected concurrent write conflict! Application intervention required.
