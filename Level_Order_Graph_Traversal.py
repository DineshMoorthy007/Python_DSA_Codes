from collections import deque

def breadth_first_search(graph: dict[str, list[str]], start_node: str) -> list[str]:
    # Initialize an empty list to record the order of visited nodes
    visited_order = []
    
    # Track discovered nodes using a set for constant-time O(1) lookups
    visited = {start_node}
    
    # Instantiate a double-ended queue initialized with the starting node
    queue = deque([start_node])

    # Continue processing as long as there are nodes waiting in the queue
    while queue:
        # Pull the oldest node out from the front of the queue
        current_node = queue.popleft()
        visited_order.append(current_node)

        # Inspect all immediate neighbors connected to the current node
        for neighbor in graph.get(current_node, []):
            if neighbor not in visited:
                # Mark neighbor as visited and commit it to the back of the queue
                visited.add(neighbor)
                queue.append(neighbor)

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
    
    print("--- Initializing Graph Traversal Engine ---")
    print(f"Starting Node: Alice")
    
    traversal_path = breadth_first_search(network_graph, "Alice")
    
    print("-" * 43)
    print(f"[SUCCESS] BFS Traversal Path: {traversal_path}")

# Output :
# --- Initializing Graph Traversal Engine ---
# Starting Node: Alice
# -------------------------------------------
# [SUCCESS] BFS Traversal Path: ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']
