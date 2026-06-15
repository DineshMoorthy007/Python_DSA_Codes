def rabin_karp_search(text: str, pattern: str, prime: int = 101) -> list[int]:
    """Finds all occurrences of a pattern inside a text using a rolling hash.
    
    This function utilizes the Rabin-Karp algorithm to achieve highly efficient
    pattern matching. It maps string windows to numerical hash values, sliding
    the window across the text in linear time by calculating the next hash values
    algebraically based on the omitted and newly appended characters.
    
    Args:
        text: The source string body to search through.
        pattern: The target substring pattern to locate.
        prime: A prime number used for the modulo hash reduction (default: 101).
        
    Returns:
        A list of starting index positions where the pattern matches the text.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    # Number of characters in the input alphabet (Standard ASCII)
    alphabet_size = 256
    
    pattern_hash = 0
    window_hash = 0
    match_indices = []
    
    # The value of h would be "pow(alphabet_size, m-1) % prime"
    h = 1
    for i in range(m - 1):
        h = (h * alphabet_size) % prime

    # Step 1: Calculate the initial hash values for both the pattern 
    # and the very first window of the text
    for i in range(m):
        pattern_hash = (alphabet_size * pattern_hash + ord(pattern[i])) % prime
        window_hash = (alphabet_size * window_hash + ord(text[i])) % prime

    # Step 2: Slide the pattern over the text window by window
    for i in range(n - m + 1):
        # If the hash values match, verify character-by-character to eliminate spurious hits
        if pattern_hash == window_hash:
            if text[i : i + m] == pattern:
                match_indices.append(i)

        # Calculate hash value for the next window of text:
        # Remove the leading digit, shift left, add the trailing digit
        if i < n - m:
            window_hash = (alphabet_size * (window_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            
            # Convert negative hash results back to positive boundaries
            if window_hash < 0:
                window_hash = window_hash + prime

    return match_indices


if __name__ == "__main__":
    print("--- Initializing Rabin-Karp Search Engine ---")
    
    source_body = "GEEKS FOR GEEKS"
    target_pattern = "GEEKS"
    
    print(f"Source Text   : '{source_body}'")
    print(f"Search Target : '{target_pattern}'")
    
    results = rabin_karp_search(source_body, target_pattern)
    
    print("-" * 47)
    print(f"[SUCCESS] Pattern located at starting indices: {results}")

Output :
--- Initializing Rabin-Karp Search Engine ---
Source Text   : 'GEEKS FOR GEEKS'
Search Target : 'GEEKS'
-----------------------------------------------
[SUCCESS] Pattern located at starting indices: [0, 10]
