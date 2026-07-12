import heapq

def dijkstra(graph: dict[str, list[tuple[str, int]]], start: str) -> tuple[dict[str, int], dict[str, str]]:
    """Calculates the shortest path from a start node to all other nodes in a graph.
    
    Args:
        graph: An adjacency list mapping each node to a list of tuples (neighbor, weight).
               Example: {'A': [('B', 4), ('C', 2)]}
        start: The starting node identifier string.
        
    Returns:
        A tuple containing:
            - A dictionary mapping each node to its minimum distance from the start.
            - A dictionary tracking the parent transitions to reconstruct paths.
    """
    # Map every node to an initial distance of infinity
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # Track the path parents for reconstruction step
    parents = {node: None for node in graph}
    
    # Priority Queue elements are stored as tuple pairs: (current_distance, node_name)
    priority_queue = [(0, start)]
    
    # Track nodes that have been completely processed
    visited = set()

    while priority_queue:
        # Extract the node with the smallest calculated distance value
        current_distance, current_node = heapq.heappop(priority_queue)
        
        # If we already optimized this node, bypass evaluation loop
        if current_node in visited:
            continue
        visited.add(current_node)

        # Explore every neighbor attached to this node
        for neighbor, weight in graph.get(current_node, []):
            if neighbor in visited:
                continue
                
            # Calculate total distance traveling through the current node
            calculated_route = current_distance + weight
            
            # If the new route path is shorter, update our tracking records
            if calculated_route < distances[neighbor]:
                distances[neighbor] = calculated_route
                parents[neighbor] = current_node
                heapq.heappush(priority_queue, (calculated_route, neighbor))
                
    return distances, parents


def reconstruct_path(parents: dict[str, str], target: str) -> list[str]:
    """Backtracks through the parent map to compile the exact route taken."""
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = parents[current]
    return path[::-1]


if __name__ == "__main__":
    print("--- Initializing Dijkstra Routing Engine ---")
    
    # Adjacency list representation of a map network
    city_map = {
        "Main_Station": [("Intersection_A", 4), ("Intersection_B", 2)],
        "Intersection_A": [("Intersection_B", 1), ("Terminal_East", 5)],
        "Intersection_B": [("Intersection_A", 3), ("Terminal_East", 8), ("Terminal_West", 10)],
        "Terminal_East":  [("Terminal_West", 2)],
        "Terminal_West":  []
    }
    
    min_distances, route_history = dijkstra(city_map, start="Main_Station")
    destination = "Terminal_West"
    exact_route = reconstruct_path(route_history, destination)
    
    print("-" * 60)
    print(f"[SUCCESS] Target Destination : '{destination}'")
    print(f"[SUCCESS] Absolute Minimum Cost: {min_distances[destination]}")
    print(f"[SUCCESS] Precise Path Taken   : {' -> '.join(exact_route)}")

# Output :
# --- Initializing Dijkstra Routing Engine ---
# ------------------------------------------------------------
# [SUCCESS] Target Destination : 'Terminal_West'
# [SUCCESS] Absolute Minimum Cost: 11
# [SUCCESS] Precise Path Taken   : Main_Station -> Intersection_A -> Terminal_East -> Terminal_West
