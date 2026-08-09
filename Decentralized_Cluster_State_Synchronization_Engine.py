import random
import time
import threading
from typing import Dict, Any

class PeerNode:
    """A decentralized node that synchronizes cluster state via gossip messages."""
    
    def __init__(self, node_id: str, seed_nodes: list['PeerNode'] = None):
        self.node_id = node_id
        self.lock = threading.Lock()
        self.running = True
        
        # Local cluster state map: node_id -> {"heartbeat": int, "timestamp": float, "status": str}
        self.membership_list: Dict[str, Dict[str, Any]] = {
            self.node_id: {"heartbeat": 1, "timestamp": time.time(), "status": "ALIVE"}
        }
        
        # Peer network routing table (simulated transport layer)
        self.peers: Dict[str, 'PeerNode'] = {}
        if seed_nodes:
            for seed in seed_nodes:
                if seed.node_id != self.node_id:
                    self.peers[seed.node_id] = seed

    def register_peer(self, peer: 'PeerNode') -> None:
        """Adds a reference to an active peer node."""
        if peer.node_id != self.node_id:
            with self.lock:
                self.peers[peer.node_id] = peer

    def merge_membership_list(self, incoming_list: Dict[str, Dict[str, Any]]) -> None:
        """Merges remote state updates into the local view using heartbeat counts."""
        with self.lock:
            for peer_id, remote_state in incoming_list.items():
                if peer_id == self.node_id:
                    continue  # Ignore self-state updates from outside

                local_state = self.membership_list.get(peer_id)
                
                # Rule: Update state if incoming heartbeat is higher (newer state)
                if not local_state or remote_state["heartbeat"] > local_state["heartbeat"]:
                    self.membership_list[peer_id] = {
                        "heartbeat": remote_state["heartbeat"],
                        "timestamp": time.time(),
                        "status": remote_state["status"]
                    }

    def _gossip_round(self) -> None:
        """Selects a random peer and exchanges state vectors."""
        with self.lock:
            # Increment self heartbeat to signal liveliness
            self.membership_list[self.node_id]["heartbeat"] += 1
            self.membership_list[self.node_id]["timestamp"] = time.time()
            
            # Audit cluster for stale nodes (Failure Detector)
            now = time.time()
            for pid, info in self.membership_list.items():
                if pid != self.node_id and info["status"] == "ALIVE":
                    if now - info["timestamp"] > 1.5:  # Timeout threshold: 1.5s
                        info["status"] = "DEAD"

            # Prepare state snapshot to send
            state_snapshot = {k: v.copy() for k, v in self.membership_list.items()}
            available_peers = list(self.peers.values())

        if not available_peers:
            return

        # Gossip Rule: Select 1 random peer to share state
        target_peer = random.choice(available_peers)
        try:
            target_peer.merge_membership_list(state_snapshot)
        except Exception:
            pass  # Simulate network dropping transient packets safely

    def run_loop(self, interval: float = 0.2) -> None:
        """Main background thread execution loop driving periodic gossip."""
        while self.running:
            self._gossip_round()
            time.sleep(interval)


if __name__ == "__main__":
    print("--- Initializing Decentralized Gossip Protocol Cluster ---\n")

    # 1. Spin up initial seed node
    seed = PeerNode(node_id="node-1")
    cluster = [seed]

    # 2. Join 4 additional nodes into the cluster via the seed node
    for i in range(2, 6):
        node = PeerNode(node_id=f"node-{i}", seed_nodes=[seed])
        cluster.append(node)

    # Cross-register peer references so network links exist
    for n1 in cluster:
        for n2 in cluster:
            n1.register_peer(n2)

    # 3. Launch concurrent threads for all nodes
    threads = []
    for node in cluster:
        t = threading.Thread(target=node.run_loop, daemon=True)
        threads.append(t)
        t.start()

    print("[INGESTION] Cluster nodes exchanging state vectors via random gossip...")
    time.sleep(1.0)  # Allow gossip state to spread across the cluster

    print("\n--- Phase 1: Convergence Inspection (Node-3's View) ---")
    for pid, state in cluster[2].membership_list.items():
        print(f"  Node-3 View -> Node: {pid:<8} | Heartbeat: {state['heartbeat']:<3} | Status: {state['status']}")

    # 4. Simulate a sudden node crash (Node-5 stops gossiping)
    print("\n[FAULT INJECTION] Crashing Node-5...")
    cluster[4].running = False

    time.sleep(2.0)  # Wait for failure detector timeouts to propagate via gossip

    print("\n--- Phase 2: Post-Crash Failure Detection (Node-1's View) ---")
    for pid, state in cluster[0].membership_list.items():
        print(f"  Node-1 View -> Node: {pid:<8} | Heartbeat: {state['heartbeat']:<3} | Status: {state['status']}")

    print("-" * 65)
    print("[SUCCESS] Decentralized state convergence and failure detection complete!")

# Output :
# --- Initializing Decentralized Gossip Protocol Cluster ---

# [INGESTION] Cluster nodes exchanging state vectors via random gossip...

# --- Phase 1: Convergence Inspection (Node-3's View) ---
#   Node-3 View -> Node: node-3   | Heartbeat: 6   | Status: ALIVE
#   Node-3 View -> Node: node-4   | Heartbeat: 4   | Status: ALIVE
#   Node-3 View -> Node: node-2   | Heartbeat: 4   | Status: ALIVE
#   Node-3 View -> Node: node-1   | Heartbeat: 5   | Status: ALIVE
#   Node-3 View -> Node: node-5   | Heartbeat: 4   | Status: ALIVE

# [FAULT INJECTION] Crashing Node-5...

# --- Phase 2: Post-Crash Failure Detection (Node-1's View) ---
#   Node-1 View -> Node: node-1   | Heartbeat: 16  | Status: ALIVE
#   Node-1 View -> Node: node-2   | Heartbeat: 16  | Status: ALIVE
#   Node-1 View -> Node: node-3   | Heartbeat: 15  | Status: ALIVE
#   Node-1 View -> Node: node-4   | Heartbeat: 14  | Status: ALIVE
#   Node-1 View -> Node: node-5   | Heartbeat: 6   | Status: DEAD
# -----------------------------------------------------------------
# [SUCCESS] Decentralized state convergence and failure detection complete!
