import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, replicas: int = 3):
        # Number of virtual nodes to create per physical server (prevents hotspots)
        self.replicas = replicas
        # Sorted list of virtual node hash positions on the ring
        self.ring: list[int] = []
        # Mapping from virtual node hash to the physical server name string
        self.vnode_map: dict[int, str] = {}

    def _hash(self, key: str) -> int:
        """Generates a standard 32-bit integer hash value for a given string."""
        sha256_hex = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return int(sha256_hex[:8], 16)

    def add_server(self, server: str) -> None:
        """Adds a physical server to the ring along with its virtual replicas."""
        for i in range(self.replicas):
            vnode_key = f"{server}-replica-{i}"
            vnode_hash = self._hash(vnode_key)
            
            # Keep the ring array sorted for binary search mapping
            bisect.insort(self.ring, vnode_hash)
            self.vnode_map[vnode_hash] = server

    def remove_server(self, server: str) -> None:
        """Removes a physical server and its associated virtual replicas from the ring."""
        for i in range(self.replicas):
            vnode_key = f"{server}-replica-{i}"
            vnode_hash = self._hash(vnode_key)
            
            # Remove from the tracking ring and the map
            if vnode_hash in self.vnode_map:
                self.ring.remove(vnode_hash)
                del self.vnode_map[vnode_hash]

    def get_server(self, data_key: str) -> str | None:
        """Routes an incoming data key to the nearest clockwise server on the ring."""
        if not self.ring:
            return None

        key_hash = self._hash(data_key)
        
        # Use binary search to find the first virtual node with a hash >= key_hash
        idx = bisect.bisect_right(self.ring, key_hash)
        
        # If the hash falls past the last server, wrap around to the first server (index 0)
        if idx == len(self.ring):
            idx = 0
            
        return self.vnode_map[self.ring[idx]]


if __name__ == "__main__":
    print("--- Initializing Consistent Hash Ring Router ---")
    router = ConsistentHashRing(replicas=3)

    # Adding production storage servers to the ring
    router.add_server("Server_Alpha")
    router.add_server("Server_Beta")
    router.add_server("Server_Gamma")

    # Mapping distinct dataset keys to target servers
    sample_keys = ["user_101", "session_992", "media_id_55", "payment_hash_8a"]
    print("\n[INITIAL ROUTING LOGS]")
    for k in sample_keys:
        print(f"  Key '{k}' -> Routed to: {router.get_server(k)}")

    print("-" * 55)
    print("[SERVER CRASH] Removing Server_Beta from cluster...")
    router.remove_server("Server_Beta")

    print("\n[POST-FAILOVER ROUTING LOGS]")
    for k in sample_keys:
        print(f"  Key '{k}' -> Routed to: {router.get_server(k)}")

# Output :
# --- Initializing Consistent Hash Ring Router ---

# [INITIAL ROUTING LOGS]
#   Key 'user_101' -> Routed to: Server_Gamma
#   Key 'session_992' -> Routed to: Server_Alpha
#   Key 'media_id_55' -> Routed to: Server_Beta
#   Key 'payment_hash_8a' -> Routed to: Server_Alpha
# -------------------------------------------------------
# [SERVER CRASH] Removing Server_Beta from cluster...

# [POST-FAILOVER ROUTING LOGS]
#   Key 'user_101' -> Routed to: Server_Gamma
#   Key 'session_992' -> Routed to: Server_Alpha
#   Key 'media_id_55' -> Routed to: Server_Alpha
#   Key 'payment_hash_8a' -> Routed to: Server_Alpha
