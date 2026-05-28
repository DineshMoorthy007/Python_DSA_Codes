class Node:
    """A single node element containing a data payload and a pointer."""
    def __init__(self, data):
        self.data = data
        self.next = None  # Pointer to the next sequential node object

class LinkedList:
    """The manager class tracking memory head references."""
    def __init__(self):
        self.head = None  # Points to the absolute first node in the sequence

    def insert_at_head(self, data):
        """Prepends a new node to the front of the list in O(1) time."""
        new_node = Node(data)
        
        # Point the new node's next property to the current head node
        new_node.next = self.head
        
        # Shift the main head pointer of the list to point to our new node
        self.head = new_node
        print(f"[INSERT] Prepended head element: {data}")

    def __str__(self):
        """Traverse the dynamic pointer chain to render a visual layout."""
        elements = []
        current = self.head
        
        while current:
            elements.append(str(current.data))
            current = current.next  # Step down the pointer path
            
        return " -> ".join(elements) + " -> None" if elements else "Empty List"

print("--- Building Dynamic Linked List ---")
stream = LinkedList()

stream.insert_at_head(40)
stream.insert_at_head(30)
stream.insert_at_head(20)

print("\n--- Current Memory Allocation Sequence ---")
print(stream)

# output :
# --- Building Dynamic Linked List ---
# [INSERT] Prepended head element: 40
# [INSERT] Prepended head element: 30
# [INSERT] Prepended head element: 20

# --- Current Memory Allocation Sequence ---
# 20 -> 30 -> 40 -> None
