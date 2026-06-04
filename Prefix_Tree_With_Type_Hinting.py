class TrieNode:
    """A structural block representing a single character step in the Trie."""
    def __init__(self):
        # Maps a character string to its corresponding child TrieNode
        self.children: dict[str, TrieNode] = {}
        # Flag to indicate if this character marks the completion of a full word
        self.is_end_of_word: bool = False

class Trie:
    """The manager class handling tree insertions and key lookups."""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Inserts a word into the Trie by chaining character nodes."""
        current = self.root
        for char in word:
            # If the character node doesn't exist, instantiate a new branch
            if char not in current.children:
                current.children[char] = TrieNode()
            current = current.children[char]
        
        # Mark the final character node as a complete word boundary
        current.is_end_of_word = True

    def search(self, word: str) -> bool:
        """Returns True if the exact word exists within the Trie structure."""
        current = self.root
        for char in word:
            if char not in current.children:
                return False
            current = current.children[char]
        return current.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """Returns True if there is any word in the Trie that starts with the given prefix."""
        current = self.root
        for char in prefix:
            if char not in current.children:
                return False
            current = current.children[char]
        return True


if __name__ == "__main__":
    print("--- Initializing Prefix Trie Optimization Engine ---")
    autocomplete_engine = Trie()
    
    # Seeding the tree with words sharing overlapping prefixes
    vocabulary = ["app", "apple", "apricot", "code", "coder"]
    for word in vocabulary:
        autocomplete_engine.insert(word)
        
    print(f"Seeded Words: {vocabulary}")
    print("-" * 52)
    
    # Running lookups
    print(f"[SEARCH] Exact word 'apple'?       -> {autocomplete_engine.search('apple')}")
    print(f"[SEARCH] Exact word 'apps'?        -> {autocomplete_engine.search('apps')}")
    print(f"[PREFIX] Dynamic prefix 'apr'...?  -> {autocomplete_engine.starts_with('apr')}")
    print(f"[PREFIX] Dynamic prefix 'xyz'...?  -> {autocomplete_engine.starts_with('xyz')}")

# Output :
# --- Initializing Prefix Trie Optimization Engine ---
# Seeded Words: ['app', 'apple', 'apricot', 'code', 'coder']
# ----------------------------------------------------
# [SEARCH] Exact word 'apple'?       -> True
# [SEARCH] Exact word 'apps'?        -> False
# [PREFIX] Dynamic prefix 'apr'...?  -> True
# [PREFIX] Dynamic prefix 'xyz'...?  -> False
