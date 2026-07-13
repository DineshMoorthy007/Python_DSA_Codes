def find_bridges(graph: dict[int, list[int]]) -> list[tuple[int, int]]:
    """Locates all bridge edges in an undirected graph using Tarjan's Algorithm.
    
    Runs in linear time O(V + E) by leveraging a single DFS execution pass
    paired with tracking discovery times and low-link values.
    
    Args:
        graph: An adjacency list representing an undirected graph.
        
    Returns:
        A list of tuple pairs, where each tuple represents a bridge edge.
    """
    timer = 0
    discovery_time: dict[int, int] = {}
    low_link: dict[int, int] = {}
    bridges: list[tuple[int, int]] = []

    def dfs(node: int, parent: int = -1) -> None:
        nonlocal timer
        # Initialize discovery time and low-link value for the current node
        discovery_time[node] = low_link[node] = timer
        timer += 1

        # Explore all connected neighbors
        for neighbor in graph.get(node, []):
            if neighbor == parent:
                continue  # Skip the edge leading back to the immediate parent

            if neighbor in discovery_time:
                # Back-edge case: Neighbor already visited, update local low-link
                low_link[node] = min(low_link[node], discovery_time[neighbor])
            else:
                # Forward-edge case: Neighbor is unvisited, recurse down
                dfs(neighbor, node)
                
                # Upon return, update the current node's low-link based on the child's capability
                low_link[node] = min(low_link[node], low_link[neighbor])
                
                # CRITICAL CONDITION: If the neighbor's lowest reachable node is strictly 
                # deeper than the current node's discovery time, the edge is a bridge.
                if low_link[neighbor] > discovery_time[node]:
                    bridges.append((node, neighbor))

    # Outer sweep handles completely disconnected graph components safely
    for vertex in graph:
        if vertex not in discovery_time:
            dfs(vertex)

    return bridges


if __name__ == "__main__":
    print("--- Initializing Network Vulnerability Scanner ---")
    
    # An undirected graph containing loops and a clear bridge edge linking two clusters
    # Cluster 1: (0, 1, 2) | Cluster 2: (3, 4, 5) | Bridge: 2 --- 3
    network_topology = {
        0: [1, 2],
        1: [0, 2],
        2: [0, 1, 3],  # Connection to 3 is the vulnerability
        3: [2, 4, 5],  # Connection to 2 is the vulnerability
        4: [3, 5],
        5: [3, 4]
    }
    
    detected_bridges = find_bridges(network_topology)
    
    print("-" * 55)
    print(f"[SUCCESS] Scan Complete. Critical Bridges Located: {len(detected_bridges)}")
    for source, dest in detected_bridges:
        print(f"  Critical Single Point of Failure -> Edge: ({source} <---> {dest})")

#   Output :
# --- Initializing Network Vulnerability Scanner ---
# -------------------------------------------------------
# [SUCCESS] Scan Complete. Critical Bridges Located: 1
#   Critical Single Point of Failure -> Edge: (2 <---> 3)
