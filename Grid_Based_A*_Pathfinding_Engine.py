import heapq

def heuristic(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Calculates Manhattan distance between two grid coordinates (x, y)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_search(
    grid: list[list[int]], 
    start: tuple[int, int], 
    goal: tuple[int, int]
) -> list[tuple[int, int]] | None:
    """Finds the shortest path on a grid using the A* Search Algorithm.
    
    Args:
        grid: 2D matrix where 0 represents navigable space and 1 represents obstacles.
        start: Starting grid coordinate (row, col).
        goal: Destination grid coordinate (row, col).
        
    Returns:
        A list of coordinates forming the optimal path, or None if blocked.
    """
    rows, cols = len(grid), len(grid[0])
    
    # Priority queue elements store: (f_score, (row, col))
    open_set: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(open_set, (0, start))
    
    # Maps each visited node to its most optimal predecessor
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    
    # g_score[node]: Actual exact cost to reach 'node' from start
    g_score: dict[tuple[int, int], float] = {start: 0}
    
    # f_score[node]: Estimated total cost = g_score[node] + heuristic(node, goal)
    f_score: dict[tuple[int, int], float] = {start: heuristic(start, goal)}
    
    # Track visited nodes to avoid duplicate processing
    closed_set: set[tuple[int, int]] = set()

    # Four cardinal movement directions: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while open_set:
        # Extract the node with the lowest total estimated f_score
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Target reached! Reconstruct path by walking backwards
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Return reversed path (start -> goal)

        if current in closed_set:
            continue
        closed_set.add(current)

        # Explore 4-way neighbors
        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            r, c = neighbor

            # Boundary check and obstacle check (grid value 1 = blocked wall)
            if 0 <= r < rows and 0 <= c < cols and grid[r][c] == 0:
                # Distance to adjacent step is 1 unit
                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(neighbor, float('inf')):
                    # Found a better path to this neighbor! Record it
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None  # Path is completely blocked by obstacles


if __name__ == "__main__":
    print("--- Initializing A* Pathfinding Grid Engine ---")
    
    # 0 = Walkable, 1 = Wall / Obstacle
    map_grid = [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],  # Wall blocks row 1, forcing path through column 4
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1],  # Wall blocks row 3, forcing path through column 0
        [0, 0, 0, 0, 0]
    ]

    start_pos = (0, 0)
    goal_pos = (4, 4)

    optimal_path = a_star_search(map_grid, start_pos, goal_pos)

    print("-" * 55)
    print(f"[SUCCESS] Start Position : {start_pos}")
    print(f"[SUCCESS] Goal Position  : {goal_pos}")
    print(f"[SUCCESS] Reconstructed Path ({len(optimal_path)} steps):")
    print(f"  {' -> '.join(map(str, optimal_path))}")

# Output :
# --- Initializing A* Pathfinding Grid Engine ---
# -------------------------------------------------------
# [SUCCESS] Start Position : (0, 0)
# [SUCCESS] Goal Position  : (4, 4)
# [SUCCESS] Reconstructed Path (17 steps):
#   (0, 0) -> (0, 1) -> (0, 2) -> (0, 3) -> (0, 4) -> (1, 4) -> (2, 4) -> (2, 3) -> (2, 2) -> (2, 1) -> (2, 0) -> (3, 0) -> (4, 0) -> (4, 1) -> (4, 2) -> (4, 3) -> (4, 4)
