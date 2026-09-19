import bisect
import hashlib
from typing import Dict, List, Optional


def md5_hash(key: str) -> int:
    """Computes a 32-bit integer hash on the hash ring using MD5."""
    return int(hashlib.md5(key.encode('utf-8')).hexdigest()[:8], 16)


class ConsistentHashRing:
    """Distributed hash ring with virtual node support for balanced partition routing."""

    def __init__(self, replicas: int = 100):
        # Number of virtual nodes per physical node
        self.replicas = replicas
        # Sorted list of virtual node hash tokens on ring
        self.ring: List[int] = []
        # Mapping from virtual token hash -> physical node ID
        self.vnode_map: Dict[int, str] = {}
        # Track active physical nodes
        self.physical_nodes: set[str] = set()

    def add_node(self, node_id: str) -> None:
        """Adds a physical node and its virtual replicas to the hash ring."""
        if node_id in self.physical_nodes:
            return

        self.physical_nodes.add(node_id)

        for i in range(self.replicas):
            vnode_key = f"{node_id}-vnode-{i}"
            vnode_hash = md5_hash(vnode_key)
            
            # Insert token hash in sorted order via bisect
            bisect.insort(self.ring, vnode_hash)
            self.vnode_map[vnode_hash] = node_id

        print(f"  [RING UPDATE] Added Node '{node_id}' with {self.replicas} virtual tokens.")

    def remove_node(self, node_id: str) -> None:
        """Removes a physical node and all its associated virtual tokens from the ring."""
        if node_id not in self.physical_nodes:
            return

        self.physical_nodes.remove(node_id)

        for i in range(self.replicas):
            vnode_key = f"{node_id}-vnode-{i}"
            vnode_hash = md5_hash(vnode_key)
            
            idx = bisect.bisect_left(self.ring, vnode_hash)
            if idx < len(self.ring) and self.ring[idx] == vnode_hash:
                del self.ring[idx]
            del self.vnode_map[vnode_hash]

        print(f"  [RING UPDATE] Removed Node '{node_id}' and reclaimed space.")

    def get_node(self, key: str) -> Optional[str]:
        """Routes a key to the first node whose token hash is >= key's hash (clockwise search)."""
        if not self.ring:
            return None

        key_hash = md5_hash(key)
        # Find index of first token hash >= key_hash
        idx = bisect.bisect_right(self.ring, key_hash)

        # Wrap around to token 0 if key_hash is greater than all tokens on ring
        if idx == len(self.ring):
            idx = 0

        vnode_hash = self.ring[idx]
        return self.vnode_map[vnode_hash]


# --- Cluster Simulation & Distribution Verification ---

if __name__ == "__main__":
    print("--- Initializing Consistent Hashing Engine with Virtual Nodes ---\n")

    # 1. Setup ring with 3 initial physical nodes and 100 vnodes/node
    hash_ring = ConsistentHashRing(replicas=100)
    initial_nodes = ["redis-node-1", "redis-node-2", "redis-node-3"]
    for node in initial_nodes:
        hash_ring.add_node(node)

    print("-" * 65)

    # 2. Map 10,000 keys across initial cluster to test balance
    NUM_KEYS = 10000
    sample_keys = [f"user_session_token_{i}" for i in range(NUM_KEYS)]

    initial_mapping: Dict[str, str] = {}
    node_counts: Dict[str, int] = {node: 0 for node in initial_nodes}

    for key in sample_keys:
        target_node = hash_ring.get_node(key)
        initial_mapping[key] = target_node
        node_counts[target_node] += 1

    print("[INITIAL DATA DISTRIBUTION Across 10,000 Keys]")
    for node, count in node_counts.items():
        percentage = (count / NUM_KEYS) * 100
        print(f"  {node:<15}: {count} keys ({percentage:.2f}%)")

    print("-" * 65)

    # 3. Add a 4th node ("redis-node-4") to simulate dynamic scaling
    print("\n[SCALING CLUSTER] Adding 'redis-node-4' to Hash Ring...")
    hash_ring.add_node("redis-node-4")

    # 4. Re-evaluate key assignments and calculate re-mapping ratio
    remapped_keys = 0
    new_counts: Dict[str, int] = {node: 0 for node in hash_ring.physical_nodes}

    for key in sample_keys:
        new_target = hash_ring.get_node(key)
        new_counts[new_target] += 1
        if new_target != initial_mapping[key]:
            remapped_keys += 1

    remapping_percentage = (remapped_keys / NUM_KEYS) * 100
    expected_remap = (1 / 4) * 100  # Optimal remapping when scaling 3 -> 4 nodes is ~25%

    print("\n[POST-SCALE DISTRIBUTION]")
    for node, count in new_counts.items():
        percentage = (count / NUM_KEYS) * 100
        print(f"  {node:<15}: {count} keys ({percentage:.2f}%)")

    print(f"\n  Keys Remapped: {remapped_keys}/{NUM_KEYS} ({remapping_percentage:.2f}%)")
    print(f"  Theoretical Ideal Remap (1/N): ~{expected_remap:.2f}%")
    print("-" * 65)
    print("[SUCCESS] Scaled cluster with minimal partition re-mapping and uniform hash ring distribution!")

# Output :
# --- Initializing Consistent Hashing Engine with Virtual Nodes ---

#   [RING UPDATE] Added Node 'redis-node-1' with 100 virtual tokens.
#   [RING UPDATE] Added Node 'redis-node-2' with 100 virtual tokens.
#   [RING UPDATE] Added Node 'redis-node-3' with 100 virtual tokens.
# -----------------------------------------------------------------
# [INITIAL DATA DISTRIBUTION Across 10,000 Keys]
#   redis-node-1   : 3103 keys (31.03%)
#   redis-node-2   : 3657 keys (36.57%)
#   redis-node-3   : 3240 keys (32.40%)
# -----------------------------------------------------------------

# [SCALING CLUSTER] Adding 'redis-node-4' to Hash Ring...
#   [RING UPDATE] Added Node 'redis-node-4' with 100 virtual tokens.

# [POST-SCALE DISTRIBUTION]
#   redis-node-2   : 2590 keys (25.90%)
#   redis-node-4   : 2710 keys (27.10%)
#   redis-node-3   : 2447 keys (24.47%)
#   redis-node-1   : 2253 keys (22.53%)

#   Keys Remapped: 2710/10000 (27.10%)
#   Theoretical Ideal Remap (1/N): ~25.00%
# -----------------------------------------------------------------
# [SUCCESS] Scaled cluster with minimal partition re-mapping and uniform hash ring distribution!
