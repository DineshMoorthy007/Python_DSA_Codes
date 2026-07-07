def levenshtein_distance(source: str, target: str) -> int:
    """Calculates the minimum edit distance between two strings.
    
    Uses a space-optimized 1D row array approach to execute in O(m * n) 
    time with an O(min(m, n)) memory footprint.
    
    Args:
        source: The original input string.
        target: The desired destination string.
        
    Returns:
        The total count of insertions, deletions, or substitutions required.
    """
    # Performance Optimization: Ensure the 'target' string is the shorter one
    # This keeps our allocated memory row as small as possible
    if len(source) < len(target):
        source, target = target, source

    m, n = len(source), len(target)
    if n == 0:
        return m

    # Initialize our baseline row representing edits from an empty string
    previous_row = list(range(n + 1))
    current_row = [0] * (n + 1)

    # Step through every character of the source string
    for i in range(1, m + 1):
        # Base case: transforming 'i' characters to an empty string requires 'i' deletions
        current_row[0] = i
        
        for j in range(1, n + 1):
            if source[i - 1] == target[j - 1]:
                # Characters match: No edit cost incurred over previous diagonal state
                current_row[j] = previous_row[j - 1]
            else:
                # Mismatch: Calculate the minimum cost between three operations
                current_row[j] = 1 + min(
                    current_row[j - 1],   # Insertion
                    previous_row[j],      # Deletion
                    previous_row[j - 1]   # Substitution
                )
        
        # Slide our state down: the current row becomes the historical row for the next pass
        previous_row[:] = current_row

    return previous_row[n]


if __name__ == "__main__":
    print("--- Initializing Fuzzy String Match Engine ---")
    
    word_a = "intention"
    word_b = "execution"
    
    print(f"Source String : '{word_a}'")
    print(f"Target String : '{word_b}'")
    
    distance = levenshtein_distance(word_a, word_b)
    
    print("-" * 50)
    print(f"[SUCCESS] Levenshtein Minimum Edit Distance: {distance}")

# Output :
# --- Initializing Fuzzy String Match Engine ---
# Source String : 'intention'
# Target String : 'execution'
# --------------------------------------------------
# [SUCCESS] Levenshtein Minimum Edit Distance: 5
