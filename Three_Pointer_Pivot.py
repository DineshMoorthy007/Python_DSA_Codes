class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def insert(self, data):
        """Helper to append nodes to the front of the list."""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    def reverse(self):
        """Inverts the pointer chain in-place."""
        previous = None
        current = self.head

        while current is not None:
            next_node = current.next  # Save next address
            current.next = previous   # Turn pointer backward
            previous = current         # Slide previous forward
            current = next_node       # Slide current forward
        
        self.head = previous

    def __str__(self):
        elements = []
        curr = self.head
        while curr:
            elements.append(str(curr.data))
            curr = curr.next
        return " -> ".join(elements) + " -> None" if elements else "Empty List"

if __name__ == "__main__":
    stream = LinkedList()
    data = [2,3,4,2,1]
    
    for val in data:  
        stream.insert(val)

    print("Original Chain Structure:")
    print(stream)

    stream.reverse()

    print("\nInverted Chain Structure:")
    print(stream)

# Output :
# Original Chain Structure:
# 1 -> 2 -> 4 -> 3 -> 2 -> None

# Inverted Chain Structure:
# 2 -> 3 -> 4 -> 2 -> 1 -> None
