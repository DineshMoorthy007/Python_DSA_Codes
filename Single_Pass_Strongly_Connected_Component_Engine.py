def find_strongly_connected_components(graph: dict[int, list[int]]) -> list[list[int]]:
    """Locates all Strongly Connected Components (SCCs) in a directed graph using Tarjan's Algorithm.
    
    Runs in linear O(V + E) time via a single depth-first search pass.
    
    Args:
        graph: An adjacency list representing a directed graph.
        
    Returns:
        A list of lists, where each sub-list contains nodes forming an SCC.
    """
    index_counter = 0
    discovery_index: dict[int, int] = {}
    low_link: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    sccs: list[list[int]] = []

    def strong_connect(node: int) -> None:
        nonlocal index_counter
        
        # Initialize discovery index and low-link value for the current node
        discovery_index[node] = low_link[node] = index_counter
        index_counter += 1
        stack.append(node)
        on_stack.add(node)

        # Explore all outgoing directed neighbors
        for neighbor in graph.get(node, []):
            if neighbor not in discovery_index:
                # Neighbor has not been visited; recurse down
                strong_connect(neighbor)
                low_link[node] = min(low_link[node], low_link[neighbor])
            elif neighbor in on_stack:
                # Neighbor is already on the stack (back-edge found within current SCC)
                low_link[node] = min(low_link[node], discovery_index[neighbor])

        # If current node is the root node of an SCC, pop the component off the stack
        if low_link[node] == discovery_index[node]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            sccs.append(scc)

    # Outer sweep handles disconnected graph components safely
    for vertex in graph:
        if vertex not in discovery_index:
            strong_connect(vertex)

    return sccs


if __name__ == "__main__":
    print("--- Initializing Dependency Graph SCC Analyzer ---\n")
    
    # Directed Graph topology with cycles:
    # Component 1 (Cycle): 0 -> 1 -> 2 -> 0
    # Cross-edge:          2 -> 3
    # Component 2 (Cycle): 3 -> 4 -> 3
    # Isolated node:       5
    dependency_graph = {
        0: [1],
        1: [2],
        2: [0, 3],
        3: [4],
        4: [3],
        5: []
    }

    components = find_strongly_connected_components(dependency_graph)

    print(f"[SUCCESS] Discovered {len(components)} Strongly Connected Components:")
    print("-" * 60)
    for idx, scc in enumerate(components, 1):
        has_cycle = len(scc) > 1 or (len(scc) == 1 and scc[0] in dependency_graph.get(scc[0], []))
        cycle_status = "Cyclic Subgraph" if has_cycle else "Acyclic Single Node"
        print(f"  SCC #{idx} ({cycle_status}): Nodes {scc}")
