def calculate_frequency(data_stream: list[str]) -> dict[str, int]:
    """Builds a frequency distribution mapping table for a given data stream.
    
    This function utilizes an underlying hash map to count occurrences of items
    in linear time. By checking keys against structural memory buckets, it avoids 
    the need to scan the collection repeatedly, ensuring optimal algorithmic lookup.
    
    Args:
        data_stream: A list of string elements (e.g., log codes, user IDs, or words).
        
    Returns:
        A dictionary mapping each unique item to its total occurrence count.
    """
    # Initialize an empty dictionary to act as our frequency hash map
    frequency_map: dict[str, int] = {}

    # Iterate through the data collection exactly once
    for item in data_stream:
        # If the item exists in the map, increment its count; otherwise, seed it at 1
        if item in frequency_map:
            frequency_map[item] += 1
        else:
            frequency_map[item] = 1

    return frequency_map


if __name__ == "__main__":
    print("--- Initializing Stream Frequency Analyzer ---")
    
    # Simulating an incoming telemetry stream of system event codes
    system_logs = ["ERR_500", "INF_200", "ERR_500", "WRN_404", "INF_200", "ERR_500", "INF_200"]
    print(f"Raw Telemetry Stream: {system_logs}")
    
    distribution = calculate_frequency(system_logs)
    
    print("-" * 52)
    print("Frequency Distribution Map:")
    for event_code, total_count in distribution.items():
        print(f"  [{event_code}] -> Spotted {total_count} times")

# Output :
# --- Initializing Stream Frequency Analyzer ---
# Raw Telemetry Stream: ['ERR_500', 'INF_200', 'ERR_500', 'WRN_404', 'INF_200', 'ERR_500', 'INF_200']
# ----------------------------------------------------
# Frequency Distribution Map:
#   [ERR_500] -> Spotted 3 times
#   [INF_200] -> Spotted 3 times
#   [WRN_404] -> Spotted 1 times
