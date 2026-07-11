from enum import Enum

class NodeState(Enum):
    """Tracking states for the three-colored graph search architecture."""
    UNVISITED = 0  # White: Not yet discovered
    VISITING = 1   # Gray: Discovered, currently in the active recursion stack
    VISITED = 2    # Black: Fully explored along with all child branches


def contains_cycle(graph: dict[str, list[str]]) -> bool:
    """Detects if a directed graph contains a cyclic loop using a three-state DFS.
    
    Args:
        graph: An adjacency list mapping each node name to a list of its destinations.
        
    Returns:
        True if a cyclic loop dependency is caught, False otherwise.
    """
    # Initialize all nodes to the UNVISITED (White) baseline state
    state_registry = {node: NodeState.UNVISITED for node in graph}
    
    # Ensure nodes that are only destinations are explicitly registered
    for destinations in graph.values():
        for node in destinations:
            if node not in state_registry:
                state_registry[node] = NodeState.UNVISITED

    def dfs_has_cycle(node: str) -> bool:
        # Move the node to the active VISITING (Gray) execution pool
        state_registry[node] = NodeState.VISITING
        
        # Explore every single connected out-edge branch path
        for neighbor in graph.get(node, []):
            neighbor_state = state_registry[neighbor]
            
            # CRITICAL HIT: If a neighbor is already VISITING, we hit a back-edge loop!
            if neighbor_state == NodeState.VISITING:
                return True
                
            # If the neighbor is unvisited, dig deeper down its recursion branch
            if neighbor_state == NodeState.UNVISITED:
                if dfs_has_cycle(neighbor):
                    return True
                    
        # Completed evaluating all sub-branches: lock down node as VISITED (Black)
        state_registry[node] = NodeState.VISITED
        return False

    # Outer sweep loop handles completely disconnected sub-graphs safely
    for vertex in state_registry:
        if state_registry[vertex] == NodeState.UNVISITED:
            if dfs_has_cycle(vertex):
                return True
                
    return False


if __name__ == "__main__":
    print("--- Initializing Pipeline Dependency Scanner ---")
    
    # Graph A: Clean Directed Acyclic Graph (DAG) with no loops
    clean_pipeline = {
        "Auth_Service": ["User_Dashboard", "Database_Proxy"],
        "Database_Proxy": ["Billing_Engine"],
        "User_Dashboard": [],
        "Billing_Engine": []
    }
    
    # Graph B: Contaminated graph containing a circular deadlock path (C -> D -> E -> C)
    corrupted_pipeline = {
        "Service_A": ["Service_B"],
        "Service_B": ["Service_C"],
        "Service_C": ["Service_D"],
        "Service_D": ["Service_E"],
        "Service_E": ["Service_C"]  # Back-edge loops directly into C
    }
    
    print("-" * 50)
    print(f"Scan Clean Pipeline     -> Cycle Found? : {contains_cycle(clean_pipeline)}")
    print(f"Scan Corrupted Pipeline -> Cycle Found? : {contains_cycle(corrupted_pipeline)}")

# Output :
# --- Initializing Pipeline Dependency Scanner ---
# --------------------------------------------------
# Scan Clean Pipeline     -> Cycle Found? : False
# Scan Corrupted Pipeline -> Cycle Found? : True
