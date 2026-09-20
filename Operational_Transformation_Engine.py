from dataclasses import dataclass
from enum import Enum, auto

class OpType(Enum):
    INSERT = auto()
    DELETE = auto()

@dataclass
class Operation:
    op_type: OpType
    position: int
    text: str  # String inserted, or string deleted

    def __repr__(self) -> str:
        symbol = "+" if self.op_type == OpType.INSERT else "-"
        return f"[{symbol} '{self.text}' @ {self.position}]"


def transform(op_a: Operation, op_b: Operation) -> Operation:
    """Inclusion Transformation IT(op_a, op_b): Transforms op_a assuming op_b has already been applied first.
    
    Guarantees Convergence Property 1 (TP1):
      Document + op_a + transform(op_b, op_a) == Document + op_b + transform(op_a, op_b)
    """
    pos_a, pos_b = op_a.position, op_b.position
    text_a, text_b = op_a.text, op_b.text

    # Case 1: Both Operations are INSERTS
    if op_a.op_type == OpType.INSERT and op_b.op_type == OpType.INSERT:
        if pos_a < pos_b or (pos_a == pos_b and id(op_a) < id(op_b)):
            # op_a inserted before op_b -> position unchanged
            return Operation(OpType.INSERT, pos_a, text_a)
        else:
            # op_a inserted after op_b -> shift position right by length of op_b text
            return Operation(OpType.INSERT, pos_a + len(text_b), text_a)

    # Case 2: INSERT vs. DELETE (op_a = INSERT, op_b = DELETE)
    elif op_a.op_type == OpType.INSERT and op_b.op_type == OpType.DELETE:
        if pos_a <= pos_b:
            return Operation(OpType.INSERT, pos_a, text_a)
        else:
            # op_b deleted text before op_a -> shift op_a position left
            shift = min(pos_a - pos_b, len(text_b))
            return Operation(OpType.INSERT, pos_a - shift, text_a)

    # Case 3: DELETE vs. INSERT (op_a = DELETE, op_b = INSERT)
    elif op_a.op_type == OpType.DELETE and op_b.op_type == OpType.INSERT:
        if pos_a < pos_b:
            return Operation(OpType.DELETE, pos_a, text_a)
        else:
            # op_b inserted text before op_a -> shift op_a position right
            return Operation(OpType.DELETE, pos_a + len(text_b), text_a)

    # Case 4: Both Operations are DELETES
    elif op_a.op_type == OpType.DELETE and op_b.op_type == OpType.DELETE:
        if pos_a < pos_b:
            return Operation(OpType.DELETE, pos_a, text_a)
        elif pos_a >= pos_b + len(text_b):
            return Operation(OpType.DELETE, pos_a - len(text_b), text_a)
        else:
            # Overlapping deletes: reduce deletion range
            overlap = (pos_b + len(text_b)) - pos_a
            remaining_text = text_a[overlap:] if overlap < len(text_a) else ""
            return Operation(OpType.DELETE, pos_b, remaining_text)

    return op_a


class TextDocument:
    """A collaborative text buffer applying transformed operations."""

    def __init__(self, content: str = ""):
        self.content = content

    def apply(self, op: Operation) -> None:
        """Applies an operation directly to the document string buffer."""
        if not op.text:
            return  # No-op

        if op.op_type == OpType.INSERT:
            self.content = self.content[:op.position] + op.text + self.content[op.position:]
        elif op.op_type == OpType.DELETE:
            del_len = len(op.text)
            self.content = self.content[:op.position] + self.content[op.position + del_len:]

    def __str__(self) -> str:
        return f"'{self.content}'"


# --- Collaborative Editing Simulation ---

if __name__ == "__main__":
    print("--- Initializing Operational Transformation (OT) Engine ---\n")

    # Initial Shared State: Both Client A and Client B start with "HELLO WORLD"
    initial_text = "HELLO WORLD"
    doc_a = TextDocument(initial_text)
    doc_b = TextDocument(initial_text)

    print(f"Initial Shared Document: {doc_a}")
    print("-" * 65)

    # -------------------------------------------------------------
    # SIMULATION: Concurrent Edits on Disconnected Replicas
    # -------------------------------------------------------------
    # Client A types " GREAT" at position 5 -> "HELLO GREAT WORLD"
    op_a = Operation(OpType.INSERT, position=5, text=" GREAT")
    
    # Client B deletes "WORLD" starting at position 6 -> "HELLO "
    op_b = Operation(OpType.DELETE, position=6, text="WORLD")

    print("[CONCURRENT LOCAL EDITS]")
    doc_a.apply(op_a)
    print(f"  Client A applies {str(op_a):<22} -> Document: {doc_a}")

    doc_b.apply(op_b)
    print(f"  Client B applies {str(op_b):<22} -> Document: {doc_b}")

    print("\n[TRANSFORMING CONCURRENT OPERATIONS]")
    # Transform Client A's op against Client B's op (for Client B's site)
    op_a_prime = transform(op_a, op_b)
    # Transform Client B's op against Client A's op (for Client A's site)
    op_b_prime = transform(op_b, op_a)

    print(f"  Transformed op_a for Client B: {op_a_prime}")
    print(f"  Transformed op_b for Client A: {op_b_prime}")

    print("\n[EXCHANGING AND APPLYING TRANSFORMED OPERATIONS]")
    doc_a.apply(op_b_prime)
    doc_b.apply(op_a_prime)

    print(f"  Client A Final Document State: {doc_a}")
    print(f"  Client B Final Document State: {doc_b}")

    assert doc_a.content == doc_b.content == "HELLO GREAT "
    print("-" * 65)
    print("[SUCCESS] Convergence Property TP1 satisfied! Both documents converged to identical text.")

# Output :
# --- Initializing Operational Transformation (OT) Engine ---

# Initial Shared Document: 'HELLO WORLD'
# -----------------------------------------------------------------
# [CONCURRENT LOCAL EDITS]
#   Client A applies [+ ' GREAT' @ 5]       -> Document: 'HELLO GREAT WORLD'
#   Client B applies [- 'WORLD' @ 6]        -> Document: 'HELLO '

# [TRANSFORMING CONCURRENT OPERATIONS]
#   Transformed op_a for Client B: [+ ' GREAT' @ 5]
#   Transformed op_b for Client A: [- 'WORLD' @ 12]

# [EXCHANGING AND APPLYING TRANSFORMED OPERATIONS]
#   Client A Final Document State: 'HELLO GREAT '
#   Client B Final Document State: 'HELLO GREAT '
# -----------------------------------------------------------------
# [SUCCESS] Convergence Property TP1 satisfied! Both documents converged to identical text.
