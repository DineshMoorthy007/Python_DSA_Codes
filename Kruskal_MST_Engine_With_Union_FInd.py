class DisjointSet:
    """An optimized Disjoint-Set (Union-Find) data structure."""
    def __init__(self, elements: list[str]):
        # Each element starts out as its own parent (its own independent cluster)
        self.parent = {element: element for element in elements}
        # Rank tracks the depth of the trees to keep them balanced during unions
        self.rank = {element: 0 for element in elements}

    def find(self, item: str) -> str:
        """Finds the root representative of the cluster containing 'item'."""
        if self.parent[item] != item:
            # Path Compression Optimization: Flatten the tree structure by
            # pointing the item directly to its root representative.
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, set1: str, set2: str) -> bool:
        """Merges two distinct clusters. Returns True if a merge occurred."""
        root1 = self.find(set1)
        root2 = self.find(set2)

        if root1 == root2:
            return False  # Both items are already in the same cluster

        # Union by Rank Optimization: Attach the shorter tree beneath the taller tree
        if self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        elif self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
            
        return True


def kruskal_mst(nodes: list[str], edges: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    """Calculates the Minimum Spanning Tree using Kruskal's Greedy Algorithm."""
    mst = []
    ds = DisjointSet(nodes)

    # Step 1: Sort all edges globally in ascending order based on their weight/cost
    sorted_edges = sorted(edges, key=lambda edge: edge)

    # Step 2: Iterate through the sorted edges and greedily add safe ones
    for u, v, weight in sorted_edges:
        # If the two endpoints belong to different clusters, it's safe to connect them
        if ds.union(u, v):
            mst.append((u, v, weight))
            
        # Optimization: An MST always contains exactly (V - 1) edges
        if len(mst) == len(nodes) - 1:
            break

    return mst


if __name__ == "__main__":
    print("--- Initializing Kruskal's MST Optimization Engine ---")
    
    # A network of data centers (nodes) and the cost to link them (edges)
    data_centers = ["A", "B", "C", "D", "E"]
    infrastructure_links = [
        ("A", "B", 4), ("A", "C", 2),
        ("B", "C", 1), ("B", "D", 5),
        ("C", "D", 8), ("C", "E", 10),
        ("D", "E", 2)
    ]
    
    minimum_spanning_tree = kruskal_mst(data_centers, infrastructure_links)
    total_cost = sum(weight for _, _, weight in minimum_spanning_tree)
    
    print("-" * 54)
    print("[SUCCESS] Optimal Network Infrastructure Links Added:")
    for source, dest, cost in minimum_spanning_tree:
        print(f"  Link {source} <---> {dest} | Cost: {cost}")
    print(f"\n[SUMMARY] Minimum Cost to Connect All Nodes: {total_cost}")

# Output :
# --- Initializing Kruskal's MST Optimization Engine ---
# ------------------------------------------------------
# [SUCCESS] Optimal Network Infrastructure Links Added:
#   Link A <---> B | Cost: 4
#   Link A <---> C | Cost: 2
#   Link B <---> D | Cost: 5
#   Link C <---> E | Cost: 10

# [SUMMARY] Minimum Cost to Connect All Nodes: 21
