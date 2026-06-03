class TreeNode:
    """A structural node representing a single point in the tree hierarchical layout."""
    def __init__(self, key: int):
        self.val = key
        self.left = None   # Pointer to the left child node (smaller values)
        self.right = None  # Pointer to the right child node (larger values)

def insert_node(root: TreeNode, key: int) -> TreeNode:
    # Base Case: If the current position is empty, allocate the new node here
    if root is None:
        return TreeNode(key)

    # Recursive Step: Navigate down the tree based on value comparisons
    if key < root.val:
        root.left = insert_node(root.left, key)
    else:
        root.right = insert_node(root.right, key)

    return root

def inorder_traversal(root: TreeNode, result: list[int]) -> None:
    """Traverses the tree structure to extract values in sorted ascending order."""
    if root:
        inorder_traversal(root.left, result)
        result.append(root.val)
        inorder_traversal(root.right, result)


if __name__ == "__main__":
    print("--- Building Binary Search Tree ---")
    
    # Initialize the anchor root node
    tree_root = TreeNode(50)
    
    # Stream random elements into the sorting tree
    insert_node(tree_root, 30)
    insert_node(tree_root, 20)
    insert_node(tree_root, 40)
    insert_node(tree_root, 70)
    insert_node(tree_root, 60)
    insert_node(tree_root, 80)
    
    # Extract the sorted representation via inorder tracking
    sorted_elements = []
    inorder_traversal(tree_root, sorted_elements)
    
    print("-" * 43)
    print(f"[SUCCESS] Sorted Array Output: {sorted_elements}")

# Output :
# --- Building Binary Search Tree ---
# -------------------------------------------
# [SUCCESS] Sorted Array Output: [20, 30, 40, 50, 60, 70, 80]
