def merge_sort(arr: list[int]) -> list[int]:
    """Sorts a list of integers in ascending order using Merge Sort."""
    # Base Case: A list with 0 or 1 elements is already sorted
    if len(arr) <= 1:
        return arr

    # Divide: Find the midpoint and split the array into two halves
    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])

    # Conquer and Combine: Merge the sorted halves back together
    return merge(left_half, right_half)

def merge(left: list[int], right: list[int]) -> list[int]:
    """Merges two sorted lists into a single, fully sorted list."""
    sorted_list = []
    i = j = 0

    # Compare elements from both lists and assemble the sorted result
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            sorted_list.append(left[i])
            i += 1
        else:
            sorted_list.append(right[j])
            j += 1

    # Append any remaining elements left over from either side
    sorted_list.extend(left[i:])
    sorted_list.extend(right[j:])
    
    return sorted_list


if __name__ == "__main__":
    print("--- Initializing Merge Sort Engine ---")
    unsorted_data = [3,1,7,34,21,23,75,98,20,43,87,67]
    print(f"Raw Input Data: {unsorted_data}")
    
    sorted_data = merge_sort(unsorted_data)
    
    print("-" * 43)
    print(f"[SUCCESS] Sorted Output: {sorted_data}")

# Output :
# --- Initializing Merge Sort Engine ---
# Raw Input Data: [3, 1, 7, 34, 21, 23, 75, 98, 20, 43, 87, 67]
# -------------------------------------------
# [SUCCESS] Sorted Output: [1, 3, 7, 20, 21, 23, 34, 43, 67, 75, 87, 98]
