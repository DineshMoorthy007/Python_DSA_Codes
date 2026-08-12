from typing import Dict

class PNCounter:
    """A State-Based Positive-Negative Counter (PN-Counter) CRDT.
    
    Guarantees strong eventual numerical convergence across distributed nodes
    without requiring central consensus or distributed locks.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        # Vector P: Tracks positive increments made by each node
        self.P: Dict[str, int] = {self.node_id: 0}
        # Vector N: Tracks negative decrements made by each node
        self.N: Dict[str, int] = {self.node_id: 0}

    def increment(self, value: int = 1) -> None:
        """Increments the counter value locally by 'value'."""
        if value < 0:
            raise ValueError("Increment value must be non-negative.")
        self.P[self.node_id] = self.P.get(self.node_id, 0) + value

    def decrement(self, value: int = 1) -> None:
        """Decrements the counter value locally by 'value'."""
        if value < 0:
            raise ValueError("Decrement value must be non-negative.")
        self.N[self.node_id] = self.N.get(self.node_id, 0) + value

    def value(self) -> int:
        """Computes the current converged scalar counter value."""
        return sum(self.P.values()) - sum(self.N.values())

    def merge(self, remote_counter: 'PNCounter') -> None:
        """Merges a remote node's counter vectors using component-wise max.
        
        Merge operation properties:
          - Commutative: A.merge(B) == B.merge(A)
          - Associative: (A.merge(B)).merge(C) == A.merge(B.merge(C))
          - Idempotent:  A.merge(A) == A
        """
        # Component-wise maximum for Increment vector P
        all_p_nodes = set(self.P.keys()).union(set(remote_counter.P.keys()))
        for node in all_p_nodes:
            self.P[node] = max(self.P.get(node, 0), remote_counter.P.get(node, 0))

        # Component-wise maximum for Decrement vector N
        all_n_nodes = set(self.N.keys()).union(set(remote_counter.N.keys()))
        for node in all_n_nodes:
            self.N[node] = max(self.N.get(node, 0), remote_counter.N.get(node, 0))


if __name__ == "__main__":
    print("--- Initializing Distributed PN-Counter CRDT Engine ---\n")

    # Instantiate three decoupled cluster nodes
    node_a = PNCounter("Node-Alpha")
    node_b = PNCounter("Node-Beta")
    node_c = PNCounter("Node-Gamma")

    # 1. Independent local updates across nodes
    print("[MUTATIONS] Executing concurrent increments and decrements...")
    node_a.increment(10)  # Node A: +10
    node_b.increment(5)   # Node B: +5
    node_b.decrement(2)   # Node B: -2
    node_c.decrement(4)   # Node C: -4

    print(f"  Node Alpha Local Value : {node_a.value():>3} (Vector P: {node_a.P}, N: {node_a.N})")
    print(f"  Node Beta Local Value  : {node_b.value():>3} (Vector P: {node_b.P}, N: {node_b.N})")
    print(f"  Node Gamma Local Value : {node_c.value():>3} (Vector P: {node_c.P}, N: {node_c.N})")

    print("-" * 65)
    print("[NETWORK SYNC] Merging states across decoupled nodes...")

    # 2. Perform partial sync: Node B merges Node A's state
    node_b.merge(node_a)
    print(f"  Node Beta Post-Sync A  : {node_b.value():>3}")

    # 3. Full gossip sync: Node C merges with B, Node A merges with C
    node_c.merge(node_b)
    node_a.merge(node_c)
    node_b.merge(node_a)

    print("\n--- Final CRDT Convergence State ---")
    print(f"  Node Alpha Converged Value : {node_a.value()}")
    print(f"  Node Beta Converged Value  : {node_b.value()}")
    print(f"  Node Gamma Converged Value : {node_c.value()}")
    print("-" * 65)
    print("[SUCCESS] All distributed nodes reached exact numerical parity!")

# Output :
# --- Initializing Distributed PN-Counter CRDT Engine ---

# [MUTATIONS] Executing concurrent increments and decrements...
#   Node Alpha Local Value :  10 (Vector P: {'Node-Alpha': 10}, N: {'Node-Alpha': 0})
#   Node Beta Local Value  :   3 (Vector P: {'Node-Beta': 5}, N: {'Node-Beta': 2})
#   Node Gamma Local Value :  -4 (Vector P: {'Node-Gamma': 0}, N: {'Node-Gamma': 4})
# -----------------------------------------------------------------
# [NETWORK SYNC] Merging states across decoupled nodes...
#   Node Beta Post-Sync A  :  13

# --- Final CRDT Convergence State ---
#   Node Alpha Converged Value : 9
#   Node Beta Converged Value  : 9
#   Node Gamma Converged Value : 9
# -----------------------------------------------------------------
# [SUCCESS] All distributed nodes reached exact numerical parity!
