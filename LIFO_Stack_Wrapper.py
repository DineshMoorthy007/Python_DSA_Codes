class Stack:
    def __init__(self):
        # We use a private list under the hood to store our elements
        self._storage = []

    def push(self, item):
        """Add an item to the top of the stack."""
        self._storage.append(item)
        print(f"[PUSH] Added to stack: {item}")

    def pop(self):
        """Remove and return the top item of the stack. Raise error if empty."""
        if self.is_empty():
            return "[ERROR] Cannot pop from an empty stack!"
        item = self._storage.pop()
        print(f"  [POP] Removed from stack: {item}")
        return item

    def peek(self):
        """Look at the top item without removing it."""
        if self.is_empty():
            return None
        return self._storage[-1]

    def is_empty(self):
        """Return True if the stack is empty, False otherwise."""
        return len(self._storage) == 0

    def __str__(self):
        """Visualize the stack in the console."""
        return f"Stack View (Bottom -> Top): {self._storage}"

print("--- Initializing Custom Stack ---")
browser_history = Stack()

# Simulating a user navigating web pages
browser_history.push("google.com")
browser_history.push("github.com")
browser_history.push("python.org")

print(f"\n{browser_history}")
print(f"[PEEK] Currently viewing: {browser_history.peek()}\n")

# User clicks the 'Back' button
browser_history.pop()
print(f"{browser_history}")

# Output :
# --- Initializing Custom Stack ---
# [PUSH] Added to stack: google.com
# [PUSH] Added to stack: github.com
# [PUSH] Added to stack: python.org

# Stack View (Bottom -> Top): ['google.com', 'github.com', 'python.org']
# [PEEK] Currently viewing: python.org

#   [POP] Removed from stack: python.org
# Stack View (Bottom -> Top): ['google.com', 'github.com']
