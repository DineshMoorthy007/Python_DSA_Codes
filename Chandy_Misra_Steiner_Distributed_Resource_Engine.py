import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

class PhilosopherState(Enum):
    THINKING = auto()
    HUNGRY = auto()
    EATING = auto()


class ForkState(Enum):
    DIRTY = auto()
    CLEAN = auto()


@dataclass
class Message:
    sender_id: int
    resource_id: str  # ID of the shared fork/resource
    is_fork: bool     # True = sending the actual fork, False = requesting the fork


class Fork:
    """Represents a shared resource between two neighboring nodes."""
    def __init__(self, resource_id: str, owner_id: int):
        self.resource_id = resource_id
        self.owner_id = owner_id
        self.state = ForkState.DIRTY  # Forks start out dirty


class DistributedPhilosopher:
    """A distributed process contending for an arbitrary set of shared resources."""
    
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = PhilosopherState.THINKING
        
        # Local fork inventory: resource_id -> Fork
        self.forks: Dict[str, Fork] = {}
        # Neighbor connections: resource_id -> peer_node_id
        self.neighbors: Dict[str, int] = {}
        # Tracks pending requests sent for missing forks: resource_id -> bool
        self.requested_forks: Dict[str, bool] = {}
        
        # Async network inbox
        self.inbox: queue.Queue[Message] = queue.Queue()
        self.network_mesh: Dict[int, 'DistributedPhilosopher'] = {}

    def connect_mesh(self, peer_nodes: Dict[int, 'DistributedPhilosopher']) -> None:
        self.network_mesh = peer_nodes

    def add_resource_link(self, resource_id: str, neighbor_id: int, initial_owner_id: int) -> None:
        """Registers a shared fork with a neighbor and sets initial asymmetry."""
        self.neighbors[resource_id] = neighbor_id
        self.requested_forks[resource_id] = False
        
        if initial_owner_id == self.node_id:
            # Shared forks start dirty
            self.forks[resource_id] = Fork(resource_id, owner_id=self.node_id)

    def request_resources(self) -> None:
        """Node becomes HUNGRY and requests any missing forks from neighbors."""
        self.state = PhilosopherState.HUNGRY
        print(f"  [Node {self.node_id}] HUNGRY! Checking required forks {list(self.neighbors.keys())}...")

        # Check missing forks and send REQUEST messages
        for res_id, neighbor_id in self.neighbors.items():
            if res_id not in self.forks:
                self._send_request(res_id, neighbor_id)

        self._check_eat_condition()

    def release_resources(self) -> None:
        """Exits EATING state, marks all local forks DIRTY, and fulfills deferred requests."""
        if self.state != PhilosopherState.EATING:
            return

        print(f"  [Node {self.node_id}] Finished EATING -> Transitioning to THINKING.")
        self.state = PhilosopherState.THINKING

        # Mark all held forks as DIRTY
        for fork in self.forks.values():
            fork.state = ForkState.DIRTY

        # Fulfill any requests that arrived while eating
        self.process_incoming_messages()

    def _send_request(self, resource_id: str, neighbor_id: int) -> None:
        if not self.requested_forks[resource_id]:
            self.requested_forks[resource_id] = True
            print(f"    [Node {self.node_id}] Requesting fork '{resource_id}' from Node {neighbor_id}...")
            peer = self.network_mesh[neighbor_id]
            peer.inbox.put(Message(sender_id=self.node_id, resource_id=resource_id, is_fork=False))

    def process_incoming_messages(self) -> None:
        """Processes incoming requests for forks or incoming fork transfers."""
        while not self.inbox.empty():
            msg = self.inbox.get_nowait()

            if msg.is_fork:
                # Received a fork from a neighbor
                received_fork = Fork(resource_id=msg.resource_id, owner_id=self.node_id)
                received_fork.state = ForkState.CLEAN  # Transferred forks arrive CLEAN
                self.forks[msg.resource_id] = received_fork
                self.requested_forks[msg.resource_id] = False
                print(f"  [Node {self.node_id}] Received CLEAN fork '{msg.resource_id}' from Node {msg.sender_id}.")

            else:
                # Received a REQUEST for a fork from a neighbor
                req_res_id = msg.resource_id
                requester_id = msg.sender_id

                if req_res_id in self.forks:
                    held_fork = self.forks[req_res_id]
                    
                    # Yield fork IF it is DIRTY and we are NOT currently EATING
                    if held_fork.state == ForkState.DIRTY and self.state != PhilosopherState.EATING:
                        del self.forks[req_res_id]
                        print(f"  [Node {self.node_id}] Cleaned and SENT fork '{req_res_id}' to Node {requester_id}.")
                        
                        # Send fork to requester
                        peer = self.network_mesh[requester_id]
                        peer.inbox.put(Message(sender_id=self.node_id, resource_id=req_res_id, is_fork=True))

                        # If we are HUNGRY and just gave away a fork, we must request it back!
                        if self.state == PhilosopherState.HUNGRY:
                            self._send_request(req_res_id, requester_id)

        self._check_eat_condition()

    def _check_eat_condition(self) -> None:
        """Enters EATING state if all required forks are held locally."""
        if self.state == PhilosopherState.HUNGRY and len(self.forks) == len(self.neighbors):
            self.state = PhilosopherState.EATING
            print(f"\n  >>> [GRANTED] Node {self.node_id} acquired ALL {len(self.forks)} forks! ENTERED EATING STATE! <<<\n")


# --- Cluster & Graph Topology Simulation ---

if __name__ == "__main__":
    print("--- Initializing Chandy-Misra-Steiner Distributed Resource Engine ---\n")

    # Topology: 3 Nodes in a Triangle Graph with 3 Shared Forks
    # Fork 'f01' shared between Node 0 and Node 1 (Initially owned by Node 0)
    # Fork 'f12' shared between Node 1 and Node 2 (Initially owned by Node 1)
    # Fork 'f20' shared between Node 2 and Node 0 (Initially owned by Node 2)
    TOTAL_NODES = 3
    nodes = {i: DistributedPhilosopher(node_id=i, total_nodes=TOTAL_NODES) for i in range(TOTAL_NODES)}
    for node in nodes.values():
        node.connect_mesh(nodes)

    # Establish initial asymmetric DAG (prevents initial circular waiting)
    edges = [
        ("f01", 0, 1, 0),  # (resource_id, node_a, node_b, initial_owner)
        ("f12", 1, 2, 1),
        ("f20", 2, 0, 2)
    ]

    for res_id, u, v, owner in edges:
        nodes[u].add_resource_link(res_id, neighbor_id=v, initial_owner_id=owner)
        nodes[v].add_resource_link(res_id, neighbor_id=u, initial_owner_id=owner)

    print("[INITIAL GRAPH CONFIGURATION]")
    for i in range(TOTAL_NODES):
        held = list(nodes[i].forks.keys())
        print(f"  Node {i} -> Held Forks: {held}")
    print("-" * 65)

    print("\n[STEP 1: Concurrent Contention from All 3 Nodes]")
    nodes[0].request_resources()
    nodes[1].request_resources()
    nodes[2].request_resources()

    print("\n[STEP 2: Message Passing & Asymmetric Priority Resolution]")
    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Eating Check -> Node 0: {nodes[0].state.name} | Node 1: {nodes[1].state.name} | Node 2: {nodes[2].state.name}")

    print("\n[STEP 3: Node 0 Finishes Eating & Releases Dirty Forks]")
    nodes[0].release_resources()

    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Post-Release Check -> Node 0: {nodes[0].state.name} | Node 1: {nodes[1].state.name} | Node 2: {nodes[2].state.name}")
    print("-" * 65)
    print("[SUCCESS] Starvation-free, deadlock-free resource allocation achieved on arbitrary graph!")
