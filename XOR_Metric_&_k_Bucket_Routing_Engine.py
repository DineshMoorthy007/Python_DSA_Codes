import hashlib
import random
from dataclasses import dataclass
from typing import Dict, List


def sha1_hash(data: str) -> int:
    """Computes SHA-1 hash of string data, returning a 160-bit integer ID."""
    return int(hashlib.sha1(data.encode('utf-8')).hexdigest(), 16)


def xor_distance(id1: int, id2: int) -> int:
    """Kademlia distance metric using bitwise XOR (id1 ^ id2)."""
    return id1 ^ id2


@dataclass
class NodeContact:
    node_id: int
    ip: str
    port: int

    def __hash__(self):
        return hash(self.node_id)


class KBucket:
    """Stores up to k contacts sharing a distance range prefix [2^i, 2^(i+1))."""

    def __init__(self, k: int = 4):
        self.k = k
        self.contacts: List[NodeContact] = []

    def add(self, contact: NodeContact) -> bool:
        """Adds or refreshes contact. Returns True if inserted, False if bucket full."""
        if contact in self.contacts:
            self.contacts.remove(contact)
            self.contacts.append(contact)  # Move to back (most recently seen)
            return True

        if len(self.contacts) < self.k:
            self.contacts.append(contact)
            return True

        return False  # Bucket is full

    def get_contacts(self) -> List[NodeContact]:
        return list(self.contacts)


class KademliaRoutingTable:
    """Manages 160 k-buckets partitioned by XOR distance bit position."""

    def __init__(self, local_node_id: int, k: int = 4):
        self.local_node_id = local_node_id
        self.k = k
        # 160 buckets for 160-bit ID space
        self.buckets: List[KBucket] = [KBucket(k=self.k) for _ in range(160)]

    def _get_bucket_index(self, node_id: int) -> int:
        """Determines bucket index based on most significant bit difference."""
        distance = xor_distance(self.local_node_id, node_id)
        if distance == 0:
            return 0
        # Bit length of distance integer gives index [0..159]
        return min(159, distance.bit_length() - 1)

    def add_contact(self, contact: NodeContact) -> None:
        if contact.node_id == self.local_node_id:
            return
        idx = self._get_bucket_index(contact.node_id)
        self.buckets[idx].add(contact)

    def find_closest_nodes(self, target_id: int, count: int = 4) -> List[NodeContact]:
        """Finds the 'count' closest nodes in the routing table relative to target_id."""
        all_contacts: List[NodeContact] = []
        for bucket in self.buckets:
            all_contacts.extend(bucket.get_contacts())

        # Sort all known contacts by XOR distance to target
        all_contacts.sort(key=lambda contact: xor_distance(contact.node_id, target_id))
        return all_contacts[:count]


class KademliaDHTNode:
    """A peer-to-peer node executing Kademlia RPC lookups and value storage."""

    def __init__(self, node_id: int, ip: str, port: int, k: int = 4):
        self.contact = NodeContact(node_id, ip, port)
        self.routing_table = KademliaRoutingTable(local_node_id=node_id, k=k)
        self.kv_store: Dict[int, str] = {}
        self.network_mesh: Dict[int, 'KademliaDHTNode'] = {}

    def connect(self, peer_nodes: Dict[int, 'KademliaDHTNode']) -> None:
        self.network_mesh = peer_nodes

    def find_node_rpc(self, target_id: int) -> List[NodeContact]:
        """RPC Endpoint: Returns closest k contacts to target_id from routing table."""
        return self.routing_table.find_closest_nodes(target_id)

    def store_rpc(self, key_id: int, value: str) -> None:
        """RPC Endpoint: Stores a key-value pair locally."""
        self.kv_store[key_id] = value

    def iterative_find_node(self, target_id: int) -> List[NodeContact]:
        """Iterative routing search: queries closest nodes progressively closer to target_id."""
        shortlist = set(self.routing_table.find_closest_nodes(target_id))
        visited: set[int] = {self.contact.node_id}

        print(f"  [Iterative Lookup] Node {self.contact.node_id & 0xFFFF:04x} searching for Target {target_id & 0xFFFF:04x}...")

        while True:
            # Find closest unvisited contact in current shortlist
            unvisited = [c for c in shortlist if c.node_id not in visited]
            if not unvisited:
                break

            # Pick closest unvisited contact
            unvisited.sort(key=lambda c: xor_distance(c.node_id, target_id))
            candidate = unvisited[0]
            visited.add(candidate.node_id)

            # Query candidate for its closest contacts
            peer = self.network_mesh[candidate.node_id]
            returned_contacts = peer.find_node_rpc(target_id)

            # Learn new contacts into local routing table
            for c in returned_contacts:
                self.routing_table.add_contact(c)

            prev_size = len(shortlist)
            shortlist.update(returned_contacts)

            print(f"    Queried Peer {candidate.node_id & 0xFFFF:04x} -> Received {len(returned_contacts)} contacts.")

            # Stop if no new nodes were added
            if len(shortlist) == prev_size:
                break

        # Return final sorted k-closest contacts
        results = list(shortlist)
        results.sort(key=lambda c: xor_distance(c.node_id, target_id))
        return results[:self.routing_table.k]

    def put(self, key: str, value: str) -> None:
        """Stores value on k closest nodes to key's SHA-1 hash."""
        key_id = sha1_hash(key)
        closest_nodes = self.iterative_find_node(key_id)

        print(f"\n  [STORE KEY] Storing '{key}'='{value}' on {len(closest_nodes)} closest nodes:")
        for contact in closest_nodes:
            peer = self.network_mesh[contact.node_id]
            peer.store_rpc(key_id, value)
            print(f"    -> Stored on Node {contact.node_id & 0xFFFF:04x}")


# --- Cluster Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Kademlia DHT Overlay Network ---\n")

    # Generate 8 random P2P nodes in 160-bit ID space
    TOTAL_NODES = 8
    random.seed(42)
    node_ids = [random.getrandbits(160) for _ in range(TOTAL_NODES)]

    dht_mesh: Dict[int, KademliaDHTNode] = {}
    for i, nid in enumerate(node_ids):
        dht_mesh[nid] = KademliaDHTNode(node_id=nid, ip=f"192.168.1.{10+i}", port=8000 + i, k=3)

    for node in dht_mesh.values():
        node.connect(dht_mesh)

    # Populate routing tables by cross-introducing nodes
    for nid, node in dht_mesh.items():
        for peer_nid, peer_node in dht_mesh.items():
            if nid != peer_nid:
                node.routing_table.add_contact(peer_node.contact)

    print(f"[DHT MESH READY] {TOTAL_NODES} peers connected in 160-bit ID space.")
    print("-" * 65)

    origin_node = list(dht_mesh.values())[0]
    target_key = "distributed_systems_paper.pdf"
    key_hash = sha1_hash(target_key)

    print(f"Target Key  : '{target_key}'")
    print(f"Key SHA-1   : 0x{key_hash:040x}")
    print("-" * 65)

    # Step 1: Perform P2P Store Operation
    origin_node.put(key=target_key, value="ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco")

    print("\n[VERIFY VALUE STORED ON TARGET NODES]")
    stored_count = 0
    for node in dht_mesh.values():
        if key_hash in node.kv_store:
            stored_count += 1
            print(f"  Node 0x{node.contact.node_id & 0xFFFF:04x} holds key! Value: {node.kv_store[key_hash]}")

    print("-" * 65)
    print(f"[SUCCESS] Distributed Hash Table stored key on {stored_count} replica nodes in logarithmic lookup steps!")

# Output :
# --- Initializing Kademlia DHT Overlay Network ---

# [DHT MESH READY] 8 peers connected in 160-bit ID space.
# -----------------------------------------------------------------
# Target Key  : 'distributed_systems_paper.pdf'
# Key SHA-1   : 0xcdf4e807246ce5423e9a9a58dbc4b092f4cc9c3e
# -----------------------------------------------------------------
#   [Iterative Lookup] Node 799d searching for Target 9c3e...
#     Queried Peer 8190 -> Received 4 contacts.
#     Queried Peer 48f6 -> Received 4 contacts.

#   [STORE KEY] Storing 'distributed_systems_paper.pdf'='ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco' on 3 closest nodes:
#     -> Stored on Node 8190
#     -> Stored on Node 48f6
#     -> Stored on Node c1a6

# [VERIFY VALUE STORED ON TARGET NODES]
#   Node 0xc1a6 holds key! Value: ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
#   Node 0x48f6 holds key! Value: ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
#   Node 0x8190 holds key! Value: ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
# -----------------------------------------------------------------
# [SUCCESS] Distributed Hash Table stored key on 3 replica nodes in logarithmic lookup steps!
