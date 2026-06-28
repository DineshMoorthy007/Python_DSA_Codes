def bellman_ford(vertices: list[str], edges: list[tuple[str, str, int]], start: str) -> tuple[dict[str, int], bool]:
    """Finds the shortest path from a start vertex to all other vertices.
    
    This algorithm handles negative edge weights and flags the existence of negative cycles.
    
    Args:
        vertices: A list of all node names in the graph.
        edges: A list of tuples formatted as (source, destination, weight).
        start: The starting node identifier.
        
    Returns:
        A tuple containing:
            - A dictionary of the shortest distances to each node.
            - A boolean flag indicating if a negative cycle was detected (True if cycle exists).
    """
    # Initialize all distances to infinity, except the starting node which is 0
    distances = {vertex: float('inf') for vertex in vertices}
    distances[start] = 0

    # Step 1: Relax all edges |V| - 1 times
    # A simple path can have at most |V| - 1 edges
    for _ in range(len(vertices) - 1):
        for u, v, weight in edges:
            if distances[u] != float('inf') and distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight

    # Step 2: Check for negative-weight cycles
    # If we can still find a shorter path, a negative loop exists
    has_negative_cycle = False
    for u, v, weight in edges:
        if distances[u] != float('inf') and distances[u] + weight < distances[v]:
            has_negative_cycle = True
            break

    return distances, has_negative_cycle


if __name__ == "__main__":
    print("--- Initializing Bellman-Ford Routing Engine ---")
    
    nodes = ["A", "B", "C", "D", "E"]
    # Graph containing a negative weight edge (D -> C cost is -5)
    network_edges = [
        ("A", "B", -1), ("A", "C", 4),
        ("B", "C", 3),  ("B", "D", 2), ("B", "E", 2),
        ("D", "B", 1),  ("D", "C", -5),
        ("E", "D", -3)
    ]
    
    shortest_paths, cycle_detected = bellman_ford(nodes, network_edges, start="A")
    
    print("-" * 55)
    if cycle_detected:
        print("[WARNING] Fatal Error: Negative weight cycle detected in graph topology!")
    else:
        print("[SUCCESS] Shortest Distances From Node A:")
        for destination, distance in shortest_paths.items():
            print(f"  To Node {destination} -> Minimum Cost: {distance}")

# Output :
# --- Initializing Bellman-Ford Routing Engine ---
# -------------------------------------------------------
# [SUCCESS] Shortest Distances From Node A:
#   To Node A -> Minimum Cost: 0
#   To Node B -> Minimum Cost: -1
#   To Node C -> Minimum Cost: -7
#   To Node D -> Minimum Cost: -2
#   To Node E -> Minimum Cost: 1
