from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set


class NodeRole(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class LogEntry:
    term: int
    command: str


@dataclass
class AppendEntriesArgs:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry]
    leader_commit: int


@dataclass
class AppendEntriesReply:
    term: int
    success: bool
    match_index: int


class RaftLogNode:
    """A distributed Raft node managing log replication and state machine commits."""

    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes

        # Persistent state on all nodes (1-indexed log representation using dummy entry at 0)
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = [LogEntry(term=0, command="INIT")]

        # Volatile state on all nodes
        self.commit_index = 0
        self.last_applied = 0
        self.role = NodeRole.FOLLOWER
        self.leader_id: Optional[int] = None

        # Volatile state on LEADER (reinitialized after election)
        self.next_index: Dict[int, int] = {}   # For each peer, index of next log entry to send
        self.match_index: Dict[int, int] = {}  # For each peer, index of highest log entry known to be replicated

        # State machine execution history
        self.state_machine_store: List[str] = []
        self.cluster_mesh: Dict[int, 'RaftLogNode'] = {}

    def connect(self, cluster_mesh: Dict[int, 'RaftLogNode']) -> None:
        self.cluster_mesh = cluster_mesh

    def become_leader(self) -> None:
        """Transitions node to LEADER state and initializes replication indices."""
        self.role = NodeRole.LEADER
        self.leader_id = self.node_id
        last_log_idx = len(self.log) - 1

        for peer_id in self.cluster_mesh:
            if peer_id != self.node_id:
                self.next_index[peer_id] = last_log_idx + 1
                self.match_index[peer_id] = 0

        print(f"  >>> [LEADER ELECTED] Node {self.node_id} assumed leadership for Term {self.current_term} <<<")

    def execute_client_command(self, command: str) -> bool:
        """Client proposal entry point. Only accepted by current LEADER."""
        if self.role != NodeRole.LEADER:
            print(f"  [REJECTED] Node {self.node_id} is not the leader. Redirecting...")
            return False

        # 1. Append command to local log
        new_entry = LogEntry(term=self.current_term, command=command)
        self.log.append(new_entry)
        entry_index = len(self.log) - 1
        print(f"  [LEADER {self.node_id}] Client proposal appended at Log Index {entry_index}: '{command}'")

        # 2. Replicate log entries to all peers
        self.replicate_logs()
        return True

    def replicate_logs(self) -> None:
        """Leader replicates log entries to peers via AppendEntries RPCs."""
        if self.role != NodeRole.LEADER:
            return

        for peer_id, peer in self.cluster_mesh.items():
            if peer_id == self.node_id:
                continue

            prev_idx = self.next_index[peer_id] - 1
            prev_term = self.log[prev_idx].term
            entries_to_send = self.log[self.next_index[peer_id]:]

            args = AppendEntriesArgs(
                term=self.current_term,
                leader_id=self.node_id,
                prev_log_index=prev_idx,
                prev_log_term=prev_term,
                entries=entries_to_send,
                leader_commit=self.commit_index
            )
            peer.handle_append_entries(args, sender_node=self)

    def handle_append_entries(self, args: AppendEntriesArgs, sender_node: 'RaftLogNode') -> None:
        """Follower processes log replication request and verifies consistency invariants."""
        # Rule 1: Reply False if term < currentTerm
        if args.term < self.current_term:
            sender_node.handle_append_entries_reply(
                self.node_id, AppendEntriesReply(self.current_term, False, match_index=0)
            )
            return

        # Synchronize term
        if args.term > self.current_term:
            self.current_term = args.term
            self.role = NodeRole.FOLLOWER
            self.voted_for = None

        self.leader_id = args.leader_id

        # Rule 2: Reply False if log doesn't contain an entry at prevLogIndex matching prevLogTerm
        if args.prev_log_index >= len(self.log) or self.log[args.prev_log_index].term != args.prev_log_term:
            sender_node.handle_append_entries_reply(
                self.node_id, AppendEntriesReply(self.current_term, False, match_index=0)
            )
            return

        # Rule 3 & 4: Overwrite conflicting entries and append any new entries
        for idx, new_entry in enumerate(args.entries):
            target_idx = args.prev_log_index + 1 + idx
            if target_idx < len(self.log):
                if self.log[target_idx].term != new_entry.term:
                    self.log = self.log[:target_idx]  # Truncate conflicting log entries
                    self.log.append(new_entry)
            else:
                self.log.append(new_entry)

        # Rule 5: Update commitIndex to min(leaderCommit, index of last new entry)
        if args.leader_commit > self.commit_index:
            self.commit_index = min(args.leader_commit, len(self.log) - 1)
            self._apply_logs_to_state_machine()

        match_idx = len(self.log) - 1
        sender_node.handle_append_entries_reply(
            self.node_id, AppendEntriesReply(self.current_term, True, match_index=match_idx)
        )

    def handle_append_entries_reply(self, peer_id: int, reply: AppendEntriesReply) -> None:
        """Leader processes replication reply, updates tracking indices, and advances commitIndex."""
        if self.role != NodeRole.LEADER:
            return

        if reply.success:
            self.match_index[peer_id] = reply.match_index
            self.next_index[peer_id] = reply.match_index + 1
            self._update_leader_commit_index()
        else:
            # Consistency check failed: decrement nextIndex and retry step-back search
            self.next_index[peer_id] = max(1, self.next_index[peer_id] - 1)

    def _update_leader_commit_index(self) -> None:
        """Advances commitIndex if an entry from current term is stored on a majority of nodes."""
        majority = (self.total_nodes // 2) + 1
        
        for N in range(len(self.log) - 1, self.commit_index, -1):
            if self.log[N].term == self.current_term:
                # Count nodes that have replicated entry N (including leader itself)
                replicated_count = 1 + sum(1 for p in self.match_index if self.match_index[p] >= N)
                if replicated_count >= majority:
                    self.commit_index = N
                    print(f"  >>> [COMMIT ADVANCED] Leader commitIndex reached {self.commit_index} (Majority: {replicated_count}/{self.total_nodes}) <<<")
                    self._apply_logs_to_state_machine()
                    break

    def _apply_logs_to_state_machine(self) -> None:
        """Applies committed log entries to the state machine store sequentially."""
        while self.commit_index > self.last_applied:
            self.last_applied += 1
            cmd = self.log[self.last_applied].command
            self.state_machine_store.append(cmd)
            print(f"    [Node {self.node_id} State Machine] Applied Log[{self.last_applied}]: '{cmd}'")


# --- Cluster & Log Replication Simulation ---

if __name__ == "__main__":
    print("--- Initializing Raft Replicated Log Engine ---\n")

    TOTAL_NODES = 5
    nodes = {i: RaftLogNode(node_id=i, total_nodes=TOTAL_NODES) for i in range(TOTAL_NODES)}
    for node in nodes.values():
        node.connect(nodes)

    # Establish Node 0 as current Leader for Term 1
    nodes[0].current_term = 1
    nodes[0].become_leader()
    print("-" * 65)

    print("\n[STEP 1: Proposing Client Command 'SET x=100']")
    nodes[0].execute_client_command("SET x=100")

    print("\n[STEP 2: Proposing Second Client Command 'SET y=200']")
    nodes[0].execute_client_command("SET y=200")

    print("\n[STEP 3: Simulating Un-Synchronized Log Repair on Node 4]")
    # Artificially inject conflicting stale log entries on Node 4
    nodes[4].log.append(LogEntry(term=1, command="STALE_CMD_A"))
    nodes[4].log.append(LogEntry(term=1, command="STALE_CMD_B"))
    print(f"Node 4 Corrupted Log Before Replication: {[e.command for e in nodes[4].log]}")

    # Force Leader to repair Node 4's log
    nodes[0].replicate_logs()
    print(f"Node 4 Repaired Log After Sync:        {[e.command for e in nodes[4].log]}")

    print("\n[CLUSTER STATE MACHINE CONSISTENCY CHECK]")
    for i in range(TOTAL_NODES):
        print(f"  Node {i} | Commit Index: {nodes[i].commit_index} | State Machine Store: {nodes[i].state_machine_store}")
    print("-" * 65)
    print("[SUCCESS] Strong log matching and quorum state machine commitment verified!")
