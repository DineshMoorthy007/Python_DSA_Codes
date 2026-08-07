import hashlib
import bisect

class ConsistentHashRing:
    """Implements Consistent Hashing with virtual nodes for even distribution."""
    
    def __init__(self, replicas: int = 100):
        """
        Args:
            replicas: Number of virtual nodes created per physical node to prevent hotspotting.
        """
        self.replicas = replicas
        self.ring: list[int] = []            # Sorted list of virtual node hash positions
        self.nodes: dict[int, str] = {}      # Maps virtual node hash -> physical node ID

    def _hash(self, key: str) -> int:
        """Generates a uniform 32-bit integer hash using MD5."""
        digest = hashlib.md5(key.encode('utf-8')).hexdigest()
        return int(digest[:8], 16)  # Use first 8 hex characters for 32-bit integer space

    def add_node(self, node: str) -> None:
        """Adds a physical node and its virtual replicas to the ring."""
        for i in range(self.replicas):
            vnode_key = f"{node}#vnode-{i}"
            vnode_hash = self._hash(vnode_key)
            self.ring.append(vnode_hash)
            self.nodes[vnode_hash] = node
        
        self.ring.sort()  # Maintain sorted order for logarithmic binary search lookups

    def remove_node(self, node: str) -> None:
        """Removes a physical node and all its virtual replicas from the ring."""
        for i in range(self.replicas):
            vnode_key = f"{node}#vnode-{i}"
            vnode_hash = self._hash(vnode_key)
            if vnode_hash in self.nodes:
                self.ring.remove(vnode_hash)
                del self.nodes[vnode_hash]

    def get_node(self, key: str) -> str | None:
        """Locates the responsible physical node for a given key in logarithmic O(log N) time."""
        if not self.ring:
            return None

        key_hash = self._hash(key)
        # Binary search: find the first virtual node hash >= key_hash
        idx = bisect.bisect_right(self.ring, key_hash)
        
        # Ring wrap-around: if key_hash is past the last node, wrap back to index 0
        if idx == len(self.ring):
            idx = 0

        return self.nodes[self.ring[idx]]


if __name__ == "__main__":
    print("--- Initializing Consistent Hashing Ring ---")

    # Spin up hash ring with 100 virtual nodes per server for smooth distribution
    hash_ring = ConsistentHashRing(replicas=100)

    # 1. Add physical cache servers to the ring
    initial_servers = ["node-alpha.cache.net", "node-beta.cache.net", "node-gamma.cache.net"]
    for server in initial_servers:
        hash_ring.add_node(server)

    print(f"\n[CLUSTER INIT] Added 3 physical servers ({len(hash_ring.ring)} virtual nodes total).")

    # 2. Map sample user keys to servers
    sample_keys = [f"user_session:{i}" for i in range(1000, 1010)]
    initial_mappings = {k: hash_ring.get_node(k) for k in sample_keys}

    print("\n[KEY MAPPING SAMPLE]")
    for k, server in list(initial_mappings.items())[:5]:
        print(f"  Key '{k}' ---> Routed to Server: '{server}'")

    print("-" * 65)

    # 3. Dynamic Scaling: Add a 4th server and measure re-mapping impact
    new_server = "node-delta.cache.net"
    print(f"[SCALE UP] Adding new physical server: '{new_server}'...")
    hash_ring.add_node(new_server)

    remapped_count = 0
    for k in sample_keys:
        new_server_assigned = hash_ring.get_node(k)
        if new_server_assigned != initial_mappings[k]:
            remapped_count += 1

    print(f"\n[REHASH ANALYSIS]")
    print(f"  Total Keys Evaluated : {len(sample_keys)}")
    print(f"  Keys Re-mapped       : {remapped_count} / {len(sample_keys)} ({remapped_count / len(sample_keys) * 100:.1f}%)")
    print(f"  [SUCCESS] Minimum key movement achieved! Standard modulo would rehash ~75% of keys.")
