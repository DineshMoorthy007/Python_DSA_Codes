class TrieNode:
    """A single tracking node inside the hierarchical prefix tree."""
    def __init__(self):
        # Maps a character string to its corresponding child TrieNode
        self.children: dict[str, TrieNode] = {}
        # Flag indicates if this specific node marks the termination of a complete word
        self.is_end_of_word: bool = False


class Trie:
    """A performance-focused Trie implementation for prefix and word matching."""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Inserts a word into the prefix tree structure."""
        current = self.root
        
        # Traverse character by character down the branching tracks
        for char in word:
            if char not in current.children:
                # If the character lane doesn't exist, instantiate a new node block
                current.children[char] = TrieNode()
            current = current.children[char]
            
        # Mark the final character node as a complete word anchor
        current.is_end_of_word = True

    def search(self, word: str) -> bool:
        """Returns True if the exact word exists within the tree structure."""
        current = self.root
        
        for char in word:
            if char not in current.children:
                return False  # Branch path broken; word doesn't exist
            current = current.children[char]
            
        return current.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """Returns True if there is any word in the tree that begins with the given prefix."""
        current = self.root
        
        for char in prefix:
            if char not in current.children:
                return False  # Prefix track missing
            current = current.children[char]
            
        return True  # The full prefix sequence was matched successfully


if __name__ == "__main__":
    print("--- Initializing Prefix-Search Trie Engine ---")
    autocomplete_registry = Trie()

    # Seeding words into the structural hierarchy
    target_vocabulary = ["apple", "app", "apricot", "bandwidth", "backend"]
    print(f"Ingesting Vocabulary: {target_vocabulary}")
    
    for word in target_vocabulary:
        autocomplete_registry.insert(word)

    print("-" * 55)
    # Verification testing passes
    print(f"Exact Search: 'apple' registered? -> {autocomplete_registry.search('apple')}")
    print(f"Exact Search: 'appl' registered?  -> {autocomplete_registry.search('appl')}")
    print(f"Prefix Search: 'app' matched?     -> {autocomplete_registry.starts_with('app')}")
    print(f"Prefix Search: 'ban' matched?     -> {autocomplete_registry.starts_with('ban')}")
    print(f"Prefix Search: 'cat' matched?     -> {autocomplete_registry.starts_with('cat')}")

# Output :
# --- Initializing Prefix-Search Trie Engine ---
# Ingesting Vocabulary: ['apple', 'app', 'apricot', 'bandwidth', 'backend']
# -------------------------------------------------------
# Exact Search: 'apple' registered? -> True
# Exact Search: 'appl' registered?  -> False
# Prefix Search: 'app' matched?     -> True
# Prefix Search: 'ban' matched?     -> True
# Prefix Search: 'cat' matched?     -> False
