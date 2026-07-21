from collections import deque

def sliding_window_maximum(stream: list[int], k: int) -> list[int]:
    """Computes the maximum value for every sliding window of size k.
    
    Uses a Monotonic Deque to achieve linear O(n) time complexity.
    
    Args:
        stream: A list of numerical values representing the input stream.
        k: The sliding window size boundary.
        
    Returns:
        A list containing the maximum value recorded in each window frame.
    """
    if not stream or k <= 0:
        return []
    if k == 1:
        return stream

    # Deque stores INDEXES of elements, keeping values in strict monotonic decreasing order
    monotonic_deque: deque[int] = deque()
    window_maxima: list[int] = []

    for idx, current_value in enumerate(stream):
        # Step 1: Evict elements that fall out of the sliding window boundary
        if monotonic_deque and monotonic_deque[0] <= idx - k:
            monotonic_deque.popleft()

        # Step 2: Maintain monotonic descending property
        # Pop smaller values from the right—they can never be the max while current_value exists!
        while monotonic_deque and stream[monotonic_deque[-1]] <= current_value:
            monotonic_deque.pop()

        # Step 3: Append the current element's index
        monotonic_deque.append(idx)

        # Step 4: Cache the max value once the initial window size (k) is established
        if idx >= k - 1:
            window_maxima.append(stream[monotonic_deque[0]])

    return window_maxima


if __name__ == "__main__":
    print("--- Initializing Real-Time Sliding Window Maximum Engine ---")
    
    # Simulated telemetry stream values over time
    telemetry_stream = [1, 3, -1, -3, 5, 3, 6, 7]
    window_size = 3
    
    print(f"Input Data Stream : {telemetry_stream}")
    print(f"Sliding Window Size: k = {window_size}\n")

    max_values = sliding_window_maximum(telemetry_stream, k=window_size)
    
    print("-" * 60)
    print(f"[SUCCESS] Calculated Window Maxima: {max_values}")
    
    # Visualizing the sliding steps
    print("\n[WINDOW STEP TRACE]")
    for i in range(len(max_values)):
        sub_window = telemetry_stream[i : i + window_size]
        print(f"  Frame #{i+1}: Sub-array {sub_window} ---> Local Max: {max_values[i]}")

# Output :
# --- Initializing Real-Time Sliding Window Maximum Engine ---
# Input Data Stream : [1, 3, -1, -3, 5, 3, 6, 7]
# Sliding Window Size: k = 3

# ------------------------------------------------------------
# [SUCCESS] Calculated Window Maxima: [3, 3, 5, 5, 6, 7]
# [WINDOW STEP TRACE]
#   Frame #1: Sub-array [1, 3, -1] ---> Local Max: 3
#   Frame #2: Sub-array [3, -1, -3] ---> Local Max: 3
#   Frame #3: Sub-array [-1, -3, 5] ---> Local Max: 5
#   Frame #4: Sub-array [-3, 5, 3] ---> Local Max: 5
#   Frame #5: Sub-array [5, 3, 6] ---> Local Max: 6
#   Frame #6: Sub-array [3, 6, 7] ---> Local Max: 7
