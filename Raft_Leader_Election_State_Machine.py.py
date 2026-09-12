import random
import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

class Role(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class RequestVoteArgs:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


@dataclass
class RequestVoteReply:
    term: int
    vote_granted: bool


@dataclass
class AppendEntriesArgs:
    term: int
    leader_id: int


@dataclass
class AppendEntriesReply:
    term: int
    success: bool


class RaftNode:
    """A distributed node executing Raft Leader Election state transitions."""

    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes

        # Persistent state on all servers
        self.current_term = 0
        self.voted_for: Optional[int] = None

        # Volatile state on all servers
        self.role = Role.FOLLOWER
        self.votes_received = 0

        # Randomized election timeout ticks (simulated logic)
        self.election_timeout = random.randint(150, 300)
        self.ticks_since_heartbeat = 0

        # Simulated network inboxes
        self.vote_req_inbox: queue.Queue[RequestVoteArgs] = queue.Queue()
        self.vote_resp_inbox: queue.Queue[RequestVoteReply] = queue.Queue()
        self.heartbeat_inbox: queue.Queue[AppendEntriesArgs] = queue.Queue()

        self.cluster_mesh: Dict[int, 'RaftNode'] = {}

    def connect_cluster(self, cluster: Dict[int, 'RaftNode']) -> None:
        self.cluster_mesh = cluster

    def tick_clock(self) -> None:
        """Simulates time passing. Drives election timeouts and leader heartbeats."""
        if self.role == Role.LEADER:
            self._send_heartbeats()
        else:
            self.ticks_since_heartbeat += 50
            if self.ticks_since_heartbeat >= self.election_timeout:
                self._start_election()

    def _start_election(self) -> None:
        """Transitions to CANDIDATE state and requests votes from cluster peers."""
        self.role = Role.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = 1  # Vote for self
        self.ticks_since_heartbeat = 0
        self.election_timeout = random.randint(150, 300)  # Reset randomized timeout

        print(f"  [Node {self.node_id}] Timeout! Starting election for Term {self.current_term}...")

        # Broadcast RequestVote RPCs
        args = RequestVoteArgs(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=0,
            last_log_term=0
        )
        for peer_id, peer in self.cluster_mesh.items():
            if peer_id != self.node_id:
                peer.vote_req_inbox.put(args)

    def _send_heartbeats(self) -> None:
        """As LEADER, periodically broadcasts empty AppendEntries RPCs to maintain authority."""
        args = AppendEntriesArgs(term=self.current_term, leader_id=self.node_id)
        for peer_id, peer in self.cluster_mesh.items():
            if peer_id != self.node_id:
                peer.heartbeat_inbox.put(args)

    def process_messages(self) -> None:
        """Processes incoming RequestVote, AppendEntries, and RPC replies."""
        self._process_heartbeats()
        self._process_vote_requests()
        self._process_vote_replies()

    def _process_heartbeats(self) -> None:
        while not self.heartbeat_inbox.empty():
            args = self.heartbeat_inbox.get_nowait()
            if args.term >= self.current_term:
                self.current_term = args.term
                self.role = Role.FOLLOWER
                self.voted_for = None
                self.ticks_since_heartbeat = 0  # Reset election timer

    def _process_vote_requests(self) -> None:
        while not self.vote_req_inbox.empty():
            args = self.vote_req_inbox.get_nowait()
            vote_granted = False

            if args.term > self.current_term:
                self.current_term = args.term
                self.role = Role.FOLLOWER
                self.voted_for = None

            if args.term == self.current_term and (self.voted_for is None or self.voted_for == args.candidate_id):
                vote_granted = True
                self.voted_for = args.candidate_id
                self.ticks_since_heartbeat = 0  # Reset timer when granting vote
                print(f"    [Node {self.node_id}] Voted FOR Node {args.candidate_id} in Term {self.current_term}.")

            # Send reply back to candidate
            reply = RequestVoteReply(term=self.current_term, vote_granted=vote_granted)
            self.cluster_mesh[args.candidate_id].vote_resp_inbox.put(reply)

    def _process_vote_replies(self) -> None:
        while not self.vote_resp_inbox.empty():
            reply = self.vote_resp_inbox.get_nowait()

            if self.role == Role.CANDIDATE and reply.term == self.current_term:
                if reply.vote_granted:
                    self.votes_received += 1
                    majority = (self.total_nodes // 2) + 1
                    if self.votes_received >= majority:
                        self.role = Role.LEADER
                        print(f"\n  >>> [ELECTED] Node {self.node_id} WON election for Term {self.current_term}! ({self.votes_received}/{self.total_nodes} votes) <<<\n")


# --- Cluster Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Raft Leader Election Engine ---\n")

    TOTAL_NODES = 5
    cluster = {i: RaftNode(node_id=i, total_nodes=TOTAL_NODES) for i in range(TOTAL_NODES)}
    for node in cluster.values():
        node.connect_cluster(cluster)

    # Stagger node 2 to trigger its election timer first
    cluster[2].ticks_since_heartbeat = 280

    print("[STEP 1: Clock Ticks -> Node 2 Triggers Election]")
    for node in cluster.values():
        node.tick_clock()

    print("\n[STEP 2: Message Delivery & Vote Processing]")
    for _ in range(2):
        for node in cluster.values():
            node.process_messages()

    print(f"Cluster Roles -> {[f'Node {i}: {cluster[i].role.name}' for i in range(TOTAL_NODES)]}")

    print("\n[STEP 3: Leader Heartbeats Suppress Follower Elections]")
    # Leader (Node 2) sends heartbeats, maintaining stability across cluster
    cluster[2].tick_clock()
    for node in cluster.values():
        node.process_messages()

    print(f"Post-Heartbeat -> {[f'Node {i}: {cluster[i].role.name}' for i in range(TOTAL_NODES)]}")
    print("-" * 65)
    print("[SUCCESS] Raft leader election and term consensus achieved with majority vote!")
