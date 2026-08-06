import random
import time
import threading
from enum import Enum, auto

class NodeState(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


class RaftNode:
    """Simulates a single Raft cluster consensus node."""
    
    def __init__(self, node_id: int, peer_ids: list[int], network_hub: dict[int, 'RaftNode']):
        self.node_id = node_id
        self.peer_ids = peer_ids
        self.network_hub = network_hub  # Simulated RPC transport network

        # Persistent state on all nodes
        self.current_term = 0
        self.voted_for: int | None = None

        # Volatile state on all nodes
        self.state = NodeState.FOLLOWER
        self.votes_received = 0
        
        # Concurrency & State Locks
        self.lock = threading.Lock()
        self.heartbeat_received = False
        self.running = True

    def _reset_election_timeout(self) -> float:
        """Randomized election timeout (150ms - 300ms) prevents split-vote deadlocks."""
        return random.uniform(0.15, 0.30)

    def run_loop(self) -> None:
        """Main execution loop tracking state transitions and election timeouts."""
        while self.running:
            with self.lock:
                current_state = self.state

            if current_state == NodeState.FOLLOWER:
                timeout = self._reset_election_timeout()
                time.sleep(timeout)
                with self.lock:
                    if not self.heartbeat_received:
                        # Timeout expired without heartbeat -> Become Candidate!
                        self._start_election()
                    self.heartbeat_received = False

            elif current_state == NodeState.CANDIDATE:
                timeout = self._reset_election_timeout()
                time.sleep(timeout)
                with self.lock:
                    if self.state == NodeState.CANDIDATE:
                        # Election timed out without majority -> Retry with incremented term
                        self._start_election()

            elif current_state == NodeState.LEADER:
                # Send periodic heartbeats to maintain authority
                self._send_heartbeats()
                time.sleep(0.05)  # Heartbeat interval = 50ms

    def _start_election(self) -> None:
        """Transitions node to CANDIDATE state and requests votes from peers."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = 1  # Vote for self
        
        print(f"  [ELECTION] Node #{self.node_id} initiated election for Term {self.current_term}")

        # Broadcast RequestVote RPCs to all peers
        for peer_id in self.peer_ids:
            peer = self.network_hub.get(peer_id)
            if peer:
                # Simulate non-blocking asynchronous RPC call
                threading.Thread(
                    target=peer.handle_request_vote,
                    args=(self.current_term, self.node_id),
                    daemon=True
                ).start()

    def handle_request_vote(self, term: int, candidate_id: int) -> None:
        """RPC Handler: Processes incoming vote requests from candidates."""
        with self.lock:
            vote_granted = False

            # Rule 1: Step down if candidate term is higher than current term
            if term > self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.voted_for = None

            # Rule 2: Grant vote if term matches and node hasn't voted yet
            if term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
                self.voted_for = candidate_id
                self.heartbeat_received = True  # Reset election timer
                vote_granted = True

        if vote_granted:
            # Send vote response back to candidate
            candidate = self.network_hub.get(candidate_id)
            if candidate:
                candidate.handle_vote_response(term, True)

    def handle_vote_response(self, term: int, vote_granted: bool) -> None:
        """RPC Handler: Processes vote responses received from cluster peers."""
        with self.lock:
            if self.state == NodeState.CANDIDATE and term == self.current_term and vote_granted:
                self.votes_received += 1
                majority = (len(self.peer_ids) + 1) // 2 + 1

                if self.votes_received >= majority:
                    self.state = NodeState.LEADER
                    print(f"\n[LEADER ELECTED] Node #{self.node_id} WON ELECTION for Term {self.current_term}! (Votes: {self.votes_received})\n")

    def _send_heartbeats(self) -> None:
        """Broadcasts empty AppendEntries RPCs to assert leadership over followers."""
        for peer_id in self.peer_ids:
            peer = self.network_hub.get(peer_id)
            if peer:
                peer.handle_heartbeat(self.current_term, self.node_id)

    def handle_heartbeat(self, term: int, leader_id: int) -> None:
        """RPC Handler: Processes incoming leader heartbeats."""
        with self.lock:
            if term >= self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.voted_for = None
                self.heartbeat_received = True  # Suppress local election timer


if __name__ == "__main__":
    print("--- Initializing 5-Node Raft Consensus Cluster ---\n")

    node_ids = [1, 2, 3, 4, 5]
    network: dict[int, RaftNode] = {}

    # 1. Instantiate cluster nodes
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        network[nid] = RaftNode(node_id=nid, peer_ids=peers, network_hub=network)

    # 2. Spin up concurrent worker threads for each cluster node
    threads = []
    for node in network.values():
        t = threading.Thread(target=node.run_loop, daemon=True)
        threads.append(t)
        t.start()

    # Allow cluster time to conduct election and establish a leader
    time.sleep(1.0)

    # Clean shutdown of simulation loops
    for node in network.values():
        node.running = False

    print("-" * 65)
    print("[FINAL CLUSTER STATE]")
    for nid, node in network.items():
        print(f"  Node #{nid} -> Role: {node.state.name:<9} | Current Term: {node.current_term}")

# Output :
# --- Initializing 5-Node Raft Consensus Cluster ---

#   [ELECTION] Node #1 initiated election for Term 1

# [LEADER ELECTED] Node #1 WON ELECTION for Term 1! (Votes: 3)

# -----------------------------------------------------------------
# [FINAL CLUSTER STATE]
#   Node #1 -> Role: LEADER    | Current Term: 1
#   Node #2 -> Role: FOLLOWER  | Current Term: 1
#   Node #3 -> Role: FOLLOWER  | Current Term: 1
#   Node #4 -> Role: FOLLOWER  | Current Term: 1
#   Node #5 -> Role: FOLLOWER  | Current Term: 1
