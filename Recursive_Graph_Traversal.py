def depth_first_search(graph: dict[str, list[str]], start_node: str) -> list[str]:
    """Traverses a graph structure using the Depth-First Search algorithm."""
    visited_order = []
    visited_set = set()

    def dfs_helper(node: str):
        # Base Case: If the node has already been processed, skip it
        if node in visited_set:
            return
        
        # Action: Mark the current node as visited and log the path
        visited_set.add(node)
        visited_order.append(node)

        # Recursive Step: Dive completely into each neighbor sequentially
        for neighbor in graph.get(node, []):
            dfs_helper(neighbor)

    # Begin the recursive chain from our anchor node
    dfs_helper(start_node)
    return visited_order


if __name__ == "__main__":
    # A standard network graph mapping user profiles to their direct friends
    network_graph = {
        "Alice": ["Bob", "Charlie"],
        "Bob": ["Alice", "David", "Eve"],
        "Charlie": ["Alice", "Frank"],
        "David": ["Bob"],
        "Eve": ["Bob"],
        "Frank": ["Charlie"]
    }
    
    print("--- Initializing Depth-First Search Engine ---")
    print("Starting Node: Alice")
    
    traversal_path = depth_first_search(network_graph, "Alice")
    
    print("-" * 47)
    print(f"[SUCCESS] DFS Traversal Path: {traversal_path}")

# Output :
# --- Initializing Depth-First Search Engine ---
# Starting Node: Alice
# -----------------------------------------------
# [SUCCESS] DFS Traversal Path: ['Alice', 'Bob', 'David', 'Eve', 'Charlie', 'Frank']
