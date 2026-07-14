def depth_limited_search(graph: dict[str, list[str]], current: str, target: str, limit: int, path: list[str]) -> bool:
    """Helper method executing a depth-bounded DFS traversal."""
    path.append(current)

    # Base Case: Target element safely located
    if current == target:
        return True

    # Base Case: Max depth constraint hit, halt downward recursion path
    if limit <= 0:
        path.pop()  # Backtrack step
        return False

    # Explore outgoing edge branches within the current depth budget
    for neighbor in graph.get(current, []):
        if depth_limited_search(graph, neighbor, target, limit - 1, path):
            return True

    # Element not found down this branch: pop from stack frame and return
    path.pop()
    return False


def iterative_deepening_dfs(graph: dict[str, list[str]], start: str, target: str, max_depth: int) -> list[str]:
    """Executes an IDDFS search by progressively expanding depth limit windows.
    
    Args:
        graph: Adjacency list representation of the target network layout.
        start: Origin entry node identifier.
        target: Destination search element anchor.
        max_depth: A safety limit capping the maximum permissible depth exploration.
        
    Returns:
        The exact ordered list of node names forming the discovered path layout.
    """
    for depth in range(max_depth):
        path_tracker = []
        print(f"[SEARCH PASS] Evaluating graph layers up to Depth Limit: {depth}")
        
        if depth_limited_search(graph, start, target, depth, path_tracker):
            print(f"[FOUND] Target located successfully at layer depth {depth}!")
            return path_tracker
            
    return []  # Search boundary exhausted with zero matches


if __name__ == "__main__":
    print("--- Initializing Progressive IDDFS Search Engine ---")
    
    # A deep tree structure where an unmitigated DFS could get lost down infinite tracks
    game_state_tree = {
        "Root": ["State_A", "State_B"],
        "State_A": ["State_C", "State_D"],
        "State_B": ["State_E", "State_F"],
        "State_C": ["Deep_Deadlock_X"],
        "Deep_Deadlock_X": ["Infinite_Loop_Y"],
        "Infinite_Loop_Y": [],
        "State_D": [],
        "State_E": ["Target_Goal"],
        "State_F": [],
        "Target_Goal": []
    }
    
    origin = "Root"
    destination = "Target_Goal"
    
    optimal_path = iterative_deepening_dfs(game_state_tree, start=origin, target=destination, max_depth=10)
    
    print("-" * 65)
    print(f"[SUCCESS] Reconstructed Path Sequence: {' -> '.join(optimal_path)}")

# Output :
# --- Initializing Progressive IDDFS Search Engine ---
# [SEARCH PASS] Evaluating graph layers up to Depth Limit: 0
# [SEARCH PASS] Evaluating graph layers up to Depth Limit: 1
# [SEARCH PASS] Evaluating graph layers up to Depth Limit: 2
# [SEARCH PASS] Evaluating graph layers up to Depth Limit: 3
# [FOUND] Target located successfully at layer depth 3!
# -----------------------------------------------------------------
# [SUCCESS] Reconstructed Path Sequence: Root -> State_B -> State_E -> Target_Goal
