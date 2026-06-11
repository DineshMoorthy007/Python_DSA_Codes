def count_set_bits(n: int) -> int:
    """Counts the number of set bits (1s) in an integer's binary form.
    
    This function implements Brian Kernighan's bitwise optimization algorithm.
    By performing an in-place bitwise AND operation between the target integer 
    and its immediate predecessor, the algorithm clears the lowest set bit 
    on each iteration, bypassing redundant zeros entirely.
    
    Args:
        n: The base-10 integer to evaluate.
        
    Returns:
        The total count of active set bits (1s) found in the binary string.
    """
    set_bit_count = 0
    
    # Continue looping until all bits have been flipped to 0
    while n > 0:
        # The core bitwise transformation step
        n = n & (n - 1)
        set_bit_count += 1
        
    return set_bit_count


if __name__ == "__main__":
    print("--- Initializing Bitwise Population Count Engine ---")
    
    # Number 44 in binary layout is: 00101100
    target_number = 44
    
    print(f"Target Number (Base 10): {target_number}")
    print(f"Binary Representation:  {bin(target_number)[2:]}")
    
    active_bits = count_set_bits(target_number)
    
    print("-" * 52)
    print(f"[SUCCESS] Total Number of Set Bits (1s): {active_bits}")

# Output :
# --- Initializing Bitwise Population Count Engine ---
# Target Number (Base 10): 44
# Binary Representation:  101100
# ----------------------------------------------------
# [SUCCESS] Total Number of Set Bits (1s): 3
