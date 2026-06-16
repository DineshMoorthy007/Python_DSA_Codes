import heapq

def prim_mst(graph: dict[str, list[tuple[str, int]]], start_node: str) -> list[tuple[str, str, int]]:
    """Calculates the Minimum Spanning Tree of a graph using Prim's Algorithm.
    
    This function starts at a designated root node and greedily expands the 
    spanning tree boundary by selecting the minimum-weight edge connecting the 
    growing tree to an unvisited vertex. It leverages a min-heap priority queue 
    to maintain optimal boundary edge exploration.
    
    Args:
        graph: An adjacency list where keys are nodes and values are lists of (neighbor, weight) tuples.
        start_node: The starting vertex anchor for tree expansion.
        
    Returns:
        A list of edges forming the Minimum Spanning Tree, formatted as (from_node, to_node, weight).
    """
    mst = []
    visited = set()
    
    # Priority queue entry format: (edge_weight, from_node, to_node)
    # Start with a dummy edge pointing to the root with a cost of 0
    edges_heap = [(0, start_node, start_node)]
    
    while edges_heap and len(visited) < len(graph):
        weight, current_from, current_to = heapq.heappop(edges_heap)
        
        # If the destination node is already in our tree, skip it to prevent loops
        if current_to in visited:
            continue
            
        # Commit the vertex to our spanning tree
        visited.add(current_to)
        
        # Avoid logging the initial dummy edge to the starting node
        if current_from != current_to:
            mst.append((current_from, current_to, weight))
            
        # Inspect all neighboring edges leaking out from the newly added node
        for neighbor, edge_weight in graph.get(current_to, []):
            if neighbor not in visited:
                # Enqueue the valid frontier edge into the min-heap
                heapq.heappush(edges_heap, (edge_weight, current_to, neighbor))
                
    return mst


if __name__ == "__main__":
    print("--- Initializing Prim's MST Optimization Engine ---")
    
    # A network layout of data centers and the latency/cost to link them together
    data_network = {
        "A": [("B", 4), ("C", 2)],
        "B": [("A", 4), ("C", 1), ("D", 5)],
        "C": [("A", 2), ("B", 1), ("D", 8), ("E", 10)],
        "D": [("B", 5), ("C", 8), ("E", 2)],
        "E": [("C", 10), ("D", 2)]
    }
    
    minimum_spanning_tree = prim_mst(data_network, start_node="A")
    total_cost = sum(weight for _, _, weight in minimum_spanning_tree)
    
    print("-" * 55)
    print("[SUCCESS] Optimal Spanning Tree Infrastructure Edges:")
    for source, dest, cost in minimum_spanning_tree:
        print(f"  Link {source} <---> {dest} | Cost/Weight: {cost}")
    print(f"\n[SUMMARY] Minimum Total Cost to Connect Network: {total_cost}")

# Output :
# --- Initializing Prim's MST Optimization Engine ---
# -------------------------------------------------------
# [SUCCESS] Optimal Spanning Tree Infrastructure Edges:
#   Link A <---> C | Cost/Weight: 2
#   Link C <---> B | Cost/Weight: 1
#   Link B <---> D | Cost/Weight: 5
#   Link D <---> E | Cost/Weight: 2

# [SUMMARY] Minimum Total Cost to Connect Network: 10
