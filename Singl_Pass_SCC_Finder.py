def find_sccs(graph: dict[int, list[int]]) -> list[list[int]]:
    """Locates all Strongly Connected Components (SCCs) using Tarjan's Algorithm.
    
    Runs in linear time O(V + E) by leveraging a single DFS execution pass
    paired with a discovery log tracking array.
    
    Args:
        graph: An adjacency list mapping each integer node to its neighbors.
        
    Returns:
        A list of groups, where each group is a list of nodes forming an SCC.
    """
    # Track the global discovery timestamp counter
    index_counter = 0
    # Stores the discovery order index assigned to each vertex
    discovery_index: dict[int, int] = {}
    # Tracks the lowest reachable discovery index from the current vertex
    low_link: dict[int, int] = {}
    
    # Execution stack tracking nodes actively participating in the current SCC branch path
    stack: list[int] = []
    on_stack: set[int] = set()
    
    sccs: list[list[int]] = []

    def dfs(node: int) -> None:
        nonlocal index_counter
        # Set the initial indexes
        discovery_index[node] = index_counter
        low_link[node] = index_counter
        index_counter += 1
        
        stack.append(node)
        on_stack.add(node)

        # Explore all outgoing edge neighbor pathways
        for neighbor in graph.get(node, []):
            if neighbor not in discovery_index:
                # Neighbor hasn't been visited; run DFS on it recursively
                dfs(neighbor)
                # Tree edge update step: adjust the low-link value based on child path results
                low_link[node] = min(low_link[node], low_link[neighbor])
            elif neighbor in on_stack:
                # Back-edge update step: neighbor is on stack, meaning a cycle is detected
                low_link[node] = min(low_link[node], discovery_index[neighbor])

        # If the current node is the root anchor of an SCC group, pop the stack
        if low_link[node] == discovery_index[node]:
            current_scc = []
            while True:
                top_vertex = stack.pop()
                on_stack.remove(top_vertex)
                current_scc.append(top_vertex)
                if top_vertex == node:
                    break
            sccs.append(current_scc)

    # Invoke DFS for all unvisited nodes to ensure disconnected graphs are handled safely
    for vertex in graph:
        if vertex not in discovery_index:
            dfs(vertex)

    return sccs


if __name__ == "__main__":
    print("--- Initializing Strongly Connected Components Engine ---")
    
    # A directed graph containing cycles and distinct cluster groups
    network_topology = {
        0: [1],
        1: [2],
        2: [0, 3],  # 0, 1, 2 form a tight loop cluster
        3: [4],
        4: [5, 7],
        5: [6],
        6: [4, 7],  # 4, 5, 6 form a second loop cluster
        7: []       # 7 is an isolated sink point node
    }
    
    scc_groups = find_sccs(network_topology)
    
    print("-" * 57)
    print(f"[SUCCESS] Total Strongly Connected Components Found: {len(scc_groups)}")
    for idx, group in enumerate(scc_groups, 1):
        print(f"  SCC Cluster #{idx} -> Nodes: {group}")

Output :
--- Initializing Strongly Connected Components Engine ---
---------------------------------------------------------
[SUCCESS] Total Strongly Connected Components Found: 4
  SCC Cluster #1 -> Nodes: [7]
  SCC Cluster #2 -> Nodes: [6, 5, 4]
  SCC Cluster #3 -> Nodes: [3]
  SCC Cluster #4 -> Nodes: [2, 1, 0]
