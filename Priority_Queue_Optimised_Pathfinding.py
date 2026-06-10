import heapq

def dijkstra(graph: dict[str, list[tuple[str, int]]], start: str) -> dict[str, int]:
    # Track the absolute shortest known distance from the start node to every other node
    # Initialize all distances to infinity, except the starting node which is 0
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # Priority queue entry format: (current_shortest_distance, node_name)
    # The min-heap ensures we always evaluate the closest available node next
    priority_queue = [(0, start)]
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        
        # Optimization: Skip processing if we've already discovered a shorter path to this node
        if current_distance > distances[current_node]:
            continue
            
        # Inspect all neighboring connections and their respective edge weights
        for neighbor, weight in graph[current_node]:
            distance_through_current = current_distance + weight
            
            # Relaxation Step: If the new path is shorter, update our records and enqueue it
            if distance_through_current < distances[neighbor]:
                distances[neighbor] = distance_through_current
                heapq.heappush(priority_queue, (distance_through_current, neighbor))
                
    return distances


if __name__ == "__main__":
    # A weighted graph representing physical cities and the highway mileage between them
    city_network = {
        "Node_A": [("Node_B", 4), ("Node_C", 2)],
        "Node_B": [("Node_C", 3), ("Node_D", 2), ("Node_E", 3)],
        "Node_C": [("Node_B", 1), ("Node_D", 4), ("Node_E", 5)],
        "Node_D": [],
        "Node_E": [("Node_D", 1)]
    }
    
    print("--- Initializing Dijkstra's Pathfinding Engine ---")
    print("Origin Point: Node_A")
    
    shortest_paths = dijkstra(city_network, "Node_A")
    
    print("-" * 50)
    print(f"[SUCCESS] Shortest Distances From Node_A:")
    for destination, distance in shortest_paths.items():
        print(f"  To {destination} -> Total Cost/Distance: {distance}")

# Output :
# --- Initializing Dijkstra's Pathfinding Engine ---
# Origin Point: Node_A
# --------------------------------------------------
# [SUCCESS] Shortest Distances From Node_A:
#   To Node_A -> Total Cost/Distance: 0
#   To Node_B -> Total Cost/Distance: 3
#   To Node_C -> Total Cost/Distance: 2
#   To Node_D -> Total Cost/Distance: 5
#   To Node_E -> Total Cost/Distance: 6
