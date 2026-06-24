import random

class NetworkNode:
    """Represents an independent server inside a decentralized cluster topology."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        # The internal metadata state this node currently holds
        self.metadata_store: dict[str, str] = {}

    def receive_gossip(self, key: str, value: str) -> bool:
        """Receives a data payload. Returns True if the info is fresh and updated."""
        if self.metadata_store.get(key) != value:
            self.metadata_store[key] = value
            return True  # State updated successfully
        return False  # Information was already known (duplicate)


class GossipCluster:
    """Manages the network cluster layer and orchestrates dissemination cycles."""
    def __init__(self, total_nodes: int):
        self.nodes = {f"Node_{i}": NetworkNode(f"Node_{i}") for i in range(total_nodes)}

    def inject_update(self, target_node_id: str, key: str, value: str) -> None:
        """Manually forces a state mutation onto a single anchor entry point node."""
        self.nodes[target_node_id].receive_gossip(key, value)

    def run_gossip_cycle(self, key: str) -> int:
        """Executes a single synchronous round of decentralized peer-to-peer gossip.
        
        Each node currently holding the update picks a completely random peer 
        and attempts to push the data payload to them.
        """
        # Identify all nodes that currently possess the data key
        active_spreaders = [
            node for node in self.nodes.values() if key in node.metadata_store
        ]
        
        new_infections = 0
        node_ids = list(self.nodes.keys())

        # Each active node contacts a random partner to share the secret
        for spreader in active_spreaders:
            partner_id = random.choice(node_ids)
            # Prevent a node from gossiping to itself
            while partner_id == spreader.node_id:
                partner_id = random.choice(node_ids)
                
            partner_node = self.nodes[partner_id]
            data_value = spreader.metadata_store[key]
            
            # Transfer payload
            if partner_node.receive_gossip(key, data_value):
                new_infections += 1
                
        return len(active_spreaders)


if __name__ == "__main__":
    print("--- Initializing Decentralized Cluster Fabric ---")
    cluster_size = 50
    cluster = GossipCluster(total_nodes=cluster_size)
    
    # Injecting a critical system patch alert into Node_0
    target_key = "SYS_PATCH_v4.2"
    target_val = "DEPOLYED_ACTIVE"
    cluster.inject_update("Node_0", target_key, target_val)
    
    print(f"Total Cluster Nodes : {cluster_size}")
    print(f"Initial State       : Only Node_0 knows about '{target_key}'")
    print("-" * 55)
    
    cycle = 1
    while True:
        nodes_informed = cluster.run_gossip_cycle(target_key)
        print(f"Cycle {cycle:2d} | Nodes Informed: {nodes_informed:2d} / {cluster_size}")
        
        # Break when the data has successfully converged across 100% of the cluster
        if nodes_informed == cluster_size:
            break
        cycle += 1
        
    print("-" * 55)
    print(f"[SUCCESS] Network state converged seamlessly after {cycle} rounds.")

# Output :
# --- Initializing Decentralized Cluster Fabric ---
# Total Cluster Nodes : 50
# Initial State       : Only Node_0 knows about 'SYS_PATCH_v4.2'
# -------------------------------------------------------
# Cycle  1 | Nodes Informed:  1 / 50
# Cycle  2 | Nodes Informed:  2 / 50
# Cycle  3 | Nodes Informed:  4 / 50
# Cycle  4 | Nodes Informed:  7 / 50
# Cycle  5 | Nodes Informed: 14 / 50
# Cycle  6 | Nodes Informed: 21 / 50
# Cycle  7 | Nodes Informed: 29 / 50
# Cycle  8 | Nodes Informed: 38 / 50
# Cycle  9 | Nodes Informed: 45 / 50
# Cycle 10 | Nodes Informed: 48 / 50
# Cycle 11 | Nodes Informed: 49 / 50
# Cycle 12 | Nodes Informed: 49 / 50
# Cycle 13 | Nodes Informed: 49 / 50
# Cycle 14 | Nodes Informed: 50 / 50
# -------------------------------------------------------
# [SUCCESS] Network state converged seamlessly after 14 rounds.
