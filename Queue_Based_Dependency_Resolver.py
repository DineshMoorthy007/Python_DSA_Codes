from collections import deque

def topological_sort_kahn(graph: dict[str, list[str]]) -> list[str]:
    """Sorts a Directed Acyclic Graph (DAG) linearly using Kahn's Algorithm.
    
    Args:
        graph: An adjacency list mapping each task node to a list of its dependents.
               Example: {'A': ['B']} implies A must run before B.
               
    Returns:
        A list of task nodes arranged in a valid sequential execution order.
        
    Raises:
        ValueError: If a cyclic dependency loop is detected, making a sort impossible.
    """
    # Step 1: Calculate the in-degree (number of incoming prerequisites) for every node
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for dependent in graph[node]:
            # Make sure nodes that only appear as dependents are tracked safely
            if dependent not in in_degree:
                in_degree[dependent] = 0
            in_degree[dependent] += 1

    # Step 2: Enqueue all tasks that have an in-degree of 0 (no prerequisites)
    queue = deque([node for node in in_degree if in_degree[node] == 0])
    execution_order = []

    # Step 3: Drain the queue and systematically relax dependencies
    while queue:
        current_task = queue.popleft()
        execution_order.append(current_task)

        # Look at all tasks that depend on the completed current_task
        for dependent in graph.get(current_task, []):
            # Since current_task finished, decrement its dependent's incoming requirement count
            in_degree[dependent] -= 1
            
            # If all prerequisites are cleared, the task is unlocked and ready to queue
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Architectural Guard Rail: If the output doesn't match the total unique nodes,
    # a circular dependency deadlock exists somewhere in the network layout.
    if len(execution_order) != len(in_degree):
        raise ValueError("Fatal Exception: Dependency loop detected! Graph is not a clean DAG.")

    return execution_order


if __name__ == "__main__":
    print("--- Initializing Build Pipeline Task Resolver ---")
    
    # Adjacency List detailing a modular software compilation network layout
    # Key -> Value mapping: [Prerequisite Task] -> [List of Downstream Tasks]
    build_dependencies = {
        "Data_Model": ["Business_Logic", "Schema_Migration"],
        "Schema_Migration": ["API_Gateway"],
        "Business_Logic": ["API_Gateway", "Unit_Tests"],
        "API_Gateway": ["UI_Dashboard"],
        "Unit_Tests": [],
        "UI_Dashboard": []
    }
    
    try:
        ordered_pipeline = topological_sort_kahn(build_dependencies)
        print("-" * 60)
        print("[SUCCESS] Optimal Execution Order Generated:")
        for step, task in enumerate(ordered_pipeline, 1):
            print(f"  Step {step}: Execute -> {task}")
    except ValueError as error:
        print(f"\n[CRITICAL ERROR] {error}")

# Output :
# --- Initializing Build Pipeline Task Resolver ---
# ------------------------------------------------------------
# [SUCCESS] Optimal Execution Order Generated:
#   Step 1: Execute -> Data_Model
#   Step 2: Execute -> Business_Logic
#   Step 3: Execute -> Schema_Migration
#   Step 4: Execute -> Unit_Tests
#   Step 5: Execute -> API_Gateway
#   Step 6: Execute -> UI_Dashboard
