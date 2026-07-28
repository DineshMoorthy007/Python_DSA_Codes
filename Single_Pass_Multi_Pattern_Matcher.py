from collections import deque

class TrieNode:
    """A node in the Aho-Corasick automaton trie layout."""
    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        # Fallback pointer used when a character mismatch occurs
        self.fail: TrieNode | None = None
        # Collection of pattern strings that terminate at or match through this node
        self.outputs: list[str] = []


class AhoCorasick:
    """A multi-pattern search engine executing in linear O(N) time."""
    def __init__(self, keywords: list[str]):
        self.root = TrieNode()
        self._build_trie(keywords)
        self._build_failure_links()

    def _build_trie(self, keywords: list[str]) -> None:
        """Step 1: Insert all keyword patterns into the foundational trie structure."""
        for keyword in keywords:
            node = self.root
            for char in keyword:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.outputs.append(keyword)

    def _build_failure_links(self) -> None:
        """Step 2: Use Breadth-First Search (BFS) to map fallback links across branches."""
        queue: deque[TrieNode] = deque()

        # Root's immediate children fail back to the root node
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        # Process the rest of the tree level by level
        while queue:
            current = queue.popleft()

            for char, child in current.children.items():
                queue.append(child)
                fail_state = current.fail

                # Walk back along failure links until a matching character branch is found
                while fail_state is not None and char not in fail_state.children:
                    fail_state = fail_state.fail

                # Set the failure link for the child node
                child.fail = fail_state.children[char] if fail_state else self.root
                
                # Merge output matches from the target failure node (handles overlapping matches)
                child.outputs.extend(child.fail.outputs)

    def search(self, text: str) -> list[tuple[int, str]]:
        """Scans input text in a single pass to locate all keyword matches.
        
        Returns:
            A list of tuples: (start_index, matched_keyword).
        """
        results: list[tuple[int, str]] = []
        current = self.root

        for i, char in enumerate(text):
            # Fallback using failure links if current character fails to match
            while current is not None and char not in current.children:
                current = current.fail

            if current is None:
                current = self.root
                continue

            current = current.children[char]

            # Collect matches found at the current character offset
            for pattern in current.outputs:
                start_index = i - len(pattern) + 1
                results.append((start_index, pattern))

        return results


if __name__ == "__main__":
    print("--- Initializing Aho-Corasick Multi-Pattern Search Engine ---")
    
    # Dictionary of target search terms (including overlapping substrings)
    dictionary = ["he", "she", "his", "hers"]
    automaton = AhoCorasick(dictionary)

    input_stream = "ushers"
    print(f"Keywords to Track : {dictionary}")
    print(f"Target Text Stream : '{input_stream}'\n")

    matches = automaton.search(input_stream)
    
    print("-" * 60)
    print(f"[SUCCESS] Total Pattern Matches Located: {len(matches)}")
    for start_idx, match in matches:
        print(f"  Match Found -> Keyword '{match}' at Index Position [{start_idx}:{start_idx + len(match)}]")
