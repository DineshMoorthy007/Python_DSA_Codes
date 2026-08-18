import hashlib
from typing import List, Tuple

class MerkleProofStep:
    """Represents a single step in a Merkle audit path."""
    def __init__(self, sibling_hash: str, is_left: bool):
        self.sibling_hash = sibling_hash
        self.is_left = is_left  # True if the sibling is positioned to the left

    def __repr__(self) -> str:
        pos = "LEFT" if self.is_left else "RIGHT"
        return f"ProofStep({pos}: {self.sibling_hash[:8]}...)"


class MerkleTree:
    """A binary cryptographic Merkle Hash Tree using SHA-256."""
    
    def __init__(self, data_blocks: List[str]):
        if not data_blocks:
            raise ValueError("Data blocks list cannot be empty.")
        
        self.raw_data = list(data_blocks)
        # Leaf hashes: SHA-256 digest of each raw data block
        self.leaves = [self._hash(data) for data in data_blocks]
        # Full tree structure: level 0 = leaves, level N = [root_hash]
        self.levels: List[List[str]] = [self.leaves]
        self._build_tree()

    @staticmethod
    def _hash(data: str) -> str:
        """Calculates a SHA-256 hex digest for a string payload."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _combine_hashes(left: str, right: str) -> str:
        """Concatenates and hashes two child digests."""
        return hashlib.sha256((left + right).encode("utf-8")).hexdigest()

    def _build_tree(self) -> None:
        """Constructs the tree bottom-up by combining pairs until the root hash remains."""
        current_level = self.leaves
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes at this level, duplicate the last node
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent_hash = self._combine_hashes(left, right)
                next_level.append(parent_hash)

            self.levels.append(next_level)
            current_level = next_level

    @property
    def root(self) -> str:
        """Returns the Merkle Root hash."""
        return self.levels[-1][0]

    def generate_proof(self, data_index: int) -> Tuple[str, List[MerkleProofStep]]:
        """Generates an audit proof for the data block at 'data_index'.
        
        Returns:
            Tuple of (target_leaf_hash, list_of_sibling_proof_steps)
        """
        if not (0 <= data_index < len(self.raw_data)):
            raise IndexError("Data index out of bounds.")

        proof: List[MerkleProofStep] = []
        idx = data_index
        target_hash = self.leaves[idx]

        # Traverse levels from bottom to just below the root
        for level in self.levels[:-1]:
            # If current index is odd, sibling is to the left; if even, sibling is to the right
            is_odd = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_odd else idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                # Sibling was duplicated during tree construction
                sibling_hash = level[idx]

            proof.append(MerkleProofStep(sibling_hash=sibling_hash, is_left=is_odd))
            idx //= 2  # Move up to parent index in the next level

        return target_hash, proof

    @classmethod
    def verify_proof(cls, target_data: str, proof: List[MerkleProofStep], root_hash: str) -> bool:
        """Cryptographically verifies whether target_data belongs to a tree with root_hash.
        
        Runs in O(log N) time and requires zero knowledge of the rest of the dataset.
        """
        current_hash = cls._hash(target_data)

        for step in proof:
            if step.is_left:
                # Sibling is on the left: hash(sibling + current)
                current_hash = cls._combine_hashes(step.sibling_hash, current_hash)
            else:
                # Sibling is on the right: hash(current + sibling)
                current_hash = cls._combine_hashes(current_hash, step.sibling_hash)

        return current_hash == root_hash


if __name__ == "__main__":
    print("--- Initializing Cryptographic Merkle Tree Engine ---\n")

    # Sample transaction ledger blocks
    ledger_records = [
        "tx: Alice pays Bob $25",
        "tx: Bob pays Charlie $10",
        "tx: Charlie pays Dave $5",
        "tx: Dave pays Eve $15",
        "tx: Eve pays Frank $30"
    ]

    tree = MerkleTree(ledger_records)

    print("[MERKLE ROOT] Top-Level Root Hash:")
    print(f"  --> {tree.root}\n")
    print(f"Tree Depth : {len(tree.levels)} levels (Leaves: {len(tree.leaves)})")
    print("-" * 65)

    # 1. Generate Audit Proof for "tx: Charlie pays Dave $5" (Index 2)
    target_idx = 2
    target_item = ledger_records[target_idx]
    target_hash, audit_proof = tree.generate_proof(target_idx)

    print(f"[AUDIT PROOF GENERATION] Generating proof for index {target_idx} ('{target_item}'):")
    for step_num, step in enumerate(audit_proof, 1):
        side = "LEFT " if step.is_left else "RIGHT"
        print(f"  Level {step_num} Sibling ({side}): {step.sibling_hash}")

    # 2. Verify Valid Proof against Root Hash
    is_valid = MerkleTree.verify_proof(target_item, audit_proof, tree.root)
    print(f"\n[VERIFICATION RESULT] Proof Valid: {is_valid} (Cryptographically authentic)\n")

    # 3. Tamper Detection: Attempt verification with modified data
    tampered_data = "tx: Charlie pays Dave $5000"
    tamper_result = MerkleTree.verify_proof(tampered_data, audit_proof, tree.root)
    print(f"[TAMPER DETECTION] Verifying altered block ('{tampered_data}'):")
    print(f"  Result: {tamper_result} -> Tampered data rejected instantly!")

# Output :
# --- Initializing Cryptographic Merkle Tree Engine ---

# [MERKLE ROOT] Top-Level Root Hash:
#   --> f6ee11579b25e3d9e92fa880b2724a228cd9b1f7f3d06f1613376ecba1b76f04

# Tree Depth : 4 levels (Leaves: 5)
# -----------------------------------------------------------------
# [AUDIT PROOF GENERATION] Generating proof for index 2 ('tx: Charlie pays Dave $5'):
#   Level 1 Sibling (RIGHT): f6b840bfb1fa7d6f75332571b61b09cb9d0979e58fc3605e8272f11c80e29fc0
#   Level 2 Sibling (LEFT ): 39d6901eee747001a300e33dab24e65061a44e17a0061e5a32464f1b1f0e4eb2
#   Level 3 Sibling (RIGHT): 8a35541ed8920537945d875acd8686b45e57845e8f5edbc3639a2491991aaa08

# [VERIFICATION RESULT] Proof Valid: True (Cryptographically authentic)

# [TAMPER DETECTION] Verifying altered block ('tx: Charlie pays Dave $5000'):
#   Result: False -> Tampered data rejected instantly!
