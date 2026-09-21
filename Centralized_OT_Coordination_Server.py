from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Tuple


class OpType(Enum):
    INSERT = auto()
    DELETE = auto()


@dataclass
class Operation:
    op_type: OpType
    position: int
    text: str

    def __repr__(self) -> str:
        symbol = "+" if self.op_type == OpType.INSERT else "-"
        return f"[{symbol} '{self.text}' @ {self.position}]"


@dataclass
class ClientMessage:
    client_id: str
    client_version: int  # Revision of the document this op was generated against
    operation: Operation


def transform(op_a: Operation, op_b: Operation) -> Operation:
    """Inclusion Transformation IT(op_a, op_b): Transforms op_a assuming op_b has already been applied first."""
    pos_a, pos_b = op_a.position, op_b.position
    text_a, text_b = op_a.text, op_b.text

    # Case 1: Both Operations are INSERTS
    if op_a.op_type == OpType.INSERT and op_b.op_type == OpType.INSERT:
        if pos_a < pos_b:
            return Operation(OpType.INSERT, pos_a, text_a)
        else:
            return Operation(OpType.INSERT, pos_a + len(text_b), text_a)

    # Case 2: INSERT vs. DELETE
    elif op_a.op_type == OpType.INSERT and op_b.op_type == OpType.DELETE:
        if pos_a <= pos_b:
            return Operation(OpType.INSERT, pos_a, text_a)
        else:
            shift = min(pos_a - pos_b, len(text_b))
            return Operation(OpType.INSERT, pos_a - shift, text_a)

    # Case 3: DELETE vs. INSERT
    elif op_a.op_type == OpType.DELETE and op_b.op_type == OpType.INSERT:
        if pos_a < pos_b:
            return Operation(OpType.DELETE, pos_a, text_a)
        else:
            return Operation(OpType.DELETE, pos_a + len(text_b), text_a)

    # Case 4: Both Operations are DELETES
    elif op_a.op_type == OpType.DELETE and op_b.op_type == OpType.DELETE:
        if pos_a < pos_b:
            return Operation(OpType.DELETE, pos_a, text_a)
        elif pos_a >= pos_b + len(text_b):
            return Operation(OpType.DELETE, pos_a - len(text_b), text_a)
        else:
            overlap = (pos_b + len(text_b)) - pos_a
            remaining_text = text_a[overlap:] if overlap < len(text_a) else ""
            return Operation(OpType.DELETE, pos_b, remaining_text)

    return op_a


class CentralOTServer:
    """Coordinates canonical document history log and transforms incoming client operations."""

    def __init__(self, initial_text: str = ""):
        self.document_buffer: str = initial_text
        self.history_log: List[Operation] = []  # Canonical sequential operations
        self.client_versions: Dict[str, int] = {}  # Tracks latest version acknowledged by each client

    def register_client(self, client_id: str) -> int:
        """Registers a client and returns the current canonical revision number."""
        current_rev = len(self.history_log)
        self.client_versions[client_id] = current_rev
        return current_rev

    def receive_operation(self, msg: ClientMessage) -> Tuple[Operation, int]:
        """Processes an incoming operation from a client.
        
        Transforms the incoming operation against all committed operations in history_log
        that were applied after the client's version.
        """
        client_id = msg.client_id
        op_to_transform = msg.operation
        client_ver = msg.client_version

        print(f"  [SERVER RECV] Client '{client_id}' (base ver {client_ver}) sent op: {op_to_transform}")

        # Catch up: Transform client op against all operations committed since client_ver
        missed_ops = self.history_log[client_ver:]
        for missed_op in missed_ops:
            op_to_transform = transform(op_to_transform, missed_op)

        # Apply transformed operation to canonical server document buffer
        self._apply_to_buffer(op_to_transform)
        self.history_log.append(op_to_transform)
        new_server_version = len(self.history_log)

        # Update sender's version
        self.client_versions[client_id] = new_server_version

        print(f"    -> Transformed Op: {op_to_transform}")
        print(f"    -> New Server Rev: {new_server_version} | Document: '{self.document_buffer}'")

        return op_to_transform, new_server_version

    def _apply_to_buffer(self, op: Operation) -> None:
        if not op.text:
            return
        if op.op_type == OpType.INSERT:
            self.document_buffer = (
                self.document_buffer[:op.position] + op.text + self.document_buffer[op.position:]
            )
        elif op.op_type == OpType.DELETE:
            del_len = len(op.text)
            self.document_buffer = (
                self.document_buffer[:op.position] + self.document_buffer[op.position + del_len:]
            )


# --- Multi-Client Server Simulation ---

if __name__ == "__main__":
    print("--- Initializing Central OT Server & History Coordinator ---\n")

    server = CentralOTServer(initial_text="SHARED TEXT")
    print(f"Initial Server State: '{server.document_buffer}' (Rev 0)")
    print("-" * 65)

    # Register 2 Clients
    rev_a = server.register_client("Client_A")
    rev_b = server.register_client("Client_B")

    print("\n[SIMULATION: Client A sends edit at Rev 0]")
    # Client A inserts "MY " at start
    msg1 = ClientMessage(
        client_id="Client_A",
        client_version=0,
        operation=Operation(OpType.INSERT, position=0, text="MY ")
    )
    op1_prime, rev_1 = server.receive_operation(msg1)

    print("\n[SIMULATION: Client B sends concurrent edit generated at Rev 0 (Stale)]")
    # Client B (unaware of Client A's edit) inserts " IS COOL" at position 11
    msg2 = ClientMessage(
        client_id="Client_B",
        client_version=0,  # Stale version! Server is now at Rev 1
        operation=Operation(OpType.INSERT, position=11, text=" IS COOL")
    )
    op2_prime, rev_2 = server.receive_operation(msg2)

    print("\n[SIMULATION: Client A sends a second operation using updated Rev 1]")
    # Client A deletes "SHARED " starting at position 3
    msg3 = ClientMessage(
        client_id="Client_A",
        client_version=1,
        operation=Operation(OpType.DELETE, position=3, text="SHARED ")
    )
    op3_prime, rev_3 = server.receive_operation(msg3)

    print("-" * 65)
    print(f"FINAL CANONICAL DOCUMENT STATE: '{server.document_buffer}'")
    print(f"TOTAL COMMITTED REVISIONS    : {len(server.history_log)}")
    print("[SUCCESS] Central OT server transformed concurrent stale commits into canonical order!")

# Output :
# --- Initializing Central OT Server & History Coordinator ---

# Initial Server State: 'SHARED TEXT' (Rev 0)
# -----------------------------------------------------------------

# [SIMULATION: Client A sends edit at Rev 0]
#   [SERVER RECV] Client 'Client_A' (base ver 0) sent op: [+ 'MY ' @ 0]
#     -> Transformed Op: [+ 'MY ' @ 0]
#     -> New Server Rev: 1 | Document: 'MY SHARED TEXT'

# [SIMULATION: Client B sends concurrent edit generated at Rev 0 (Stale)]
#   [SERVER RECV] Client 'Client_B' (base ver 0) sent op: [+ ' IS COOL' @ 11]
#     -> Transformed Op: [+ ' IS COOL' @ 14]
#     -> New Server Rev: 2 | Document: 'MY SHARED TEXT IS COOL'

# [SIMULATION: Client A sends a second operation using updated Rev 1]
#   [SERVER RECV] Client 'Client_A' (base ver 1) sent op: [- 'SHARED ' @ 3]
#     -> Transformed Op: [- 'SHARED ' @ 3]
#     -> New Server Rev: 3 | Document: 'MY TEXT IS COOL'
# -----------------------------------------------------------------
# FINAL CANONICAL DOCUMENT STATE: 'MY TEXT IS COOL'
# TOTAL COMMITTED REVISIONS    : 3
# [SUCCESS] Central OT server transformed concurrent stale commits into canonical order!
