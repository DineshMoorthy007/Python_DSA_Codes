import hashlib
from bisect import bisect_right

class ConsistentHashRing:
    """Manages a distributed server cluster ring layout using Consistent Hashing."""
    def __init__(self, replicas: int = 3):
        # Number of virtual nodes to map per physical server node
        self.replicas = replicas
        # The sorted collection of hash positions on the ring map
        self.ring: list[int] = []
        # Mapping from hash position index back to the physical node name string
        self.hash_to_node: dict[int, str] = {}

    def _hash(self, key: str) -> int:
        """Internal helper generating an integer hash identifier from a string key."""
        # Using md5 for a highly balanced bit distribution space
        hash_bytes = hashlib.md5(key.encode('utf-8')).digest()
        # Extract the first 4 bytes as an integer index value
        return int.from_bytes(hash_bytes[:4], byteorder='big')

    def add_node(self, node: str) -> None:
        """Hooks a new physical node into the hash ring with virtual replicas."""
        for i in range(self.replicas):
            # Formulate a unique replica token string label
            replica_key = f"{node}-replica-{i}"
            replica_hash = self._hash(replica_key)
            
            # Map position inside the dictionary layout registry
            self.hash_to_node[replica_hash] = node
            
            # Keep the ring positions array sorted using standard binary insertions
            # Using bisect_right to trace position indexes
            idx = bisect_right(self.ring, replica_hash)
            self.ring.insert(idx, replica_hash)

    def remove_node(self, node: str) -> None:
        """Removes a physical node and its virtual replicas from the hash ring."""
        for i in range(self.replicas):
            replica_key = f"{node}-replica-{i}"
            replica_hash = self._hash(replica_key)
            
            if replica_hash in self.hash_to_node:
                del self.hash_to_node[replica_hash]
                self.ring.remove(replica_hash)

    def get_node(self, key: str) -> str | None:
        """Routes a lookup key to the nearest clockwise server node on the ring."""
        if not self.ring:
            return None

        key_hash = self._hash(key)
        
        # Use binary search to locate the first node position matching key_hash
        idx = bisect_right(self.ring, key_hash)
        
        # If we hit the end of the list array, wrap around to the first element (index 0)
        if idx == len(self.ring):
            idx = 0
            
        return self.hash_to_node[self.ring[idx]]


if __name__ == "__main__":
    print("--- Initializing Distributed Cache Hash Ring Engine ---")
    
    # Instantiate a hash ring configuration pool
    cluster_ring = ConsistentHashRing(replicas=3)
    
    # 1. Register active target hardware servers
    cluster_ring.add_node("Server_Alpha")
    cluster_ring.add_node("Server_Beta")
    cluster_ring.add_node("Server_Gamma")
    
    # 2. Map sample cache keys across the cluster topology
    sample_keys = ["user_profile_101", "session_token_xyz", "image_asset_992", "order_history_5"]
    
    print("\n[ROUTING MAP] Initial Key Distribution Strategy:")
    for data_key in sample_keys:
        target_server = cluster_ring.get_node(data_key)
        print(f"  Key '{data_key}' ---> Routed To: {target_server}")
        
    print("-" * 65)
    print("[CLUSTERING] Server_Beta encountered a crash! De-registering node...")
    cluster_ring.remove_node("Server_Beta")
    
    print("\n[RE-ROUTING] Evaluating data access paths post-crash:")
    for data_key in sample_keys:
        target_server = cluster_ring.get_node(data_key)
        print(f"  Key '{data_key}' ---> Routed To: {target_server}")

#   Output :
# --- Initializing Distributed Cache Hash Ring Engine ---

# [ROUTING MAP] Initial Key Distribution Strategy:
#   Key 'user_profile_101' ---> Routed To: Server_Alpha
#   Key 'session_token_xyz' ---> Routed To: Server_Alpha
#   Key 'image_asset_992' ---> Routed To: Server_Gamma
#   Key 'order_history_5' ---> Routed To: Server_Gamma
# -----------------------------------------------------------------
# [CLUSTERING] Server_Beta encountered a crash! De-registering node...

# [RE-ROUTING] Evaluating data access paths post-crash:
#   Key 'user_profile_101' ---> Routed To: Server_Alpha
#   Key 'session_token_xyz' ---> Routed To: Server_Alpha
#   Key 'image_asset_992' ---> Routed To: Server_Gamma
#   Key 'order_history_5' ---> Routed To: Server_Gamma
