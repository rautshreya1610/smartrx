"""
trie.py
=======
Trie (Prefix Tree) Data Structure for Fast Medicine Name Search.

HOW IT WORKS:
- Each character of a medicine name becomes a node in the tree.
- Searching for prefix "para" jumps directly to all names starting with "para".
- Time Complexity: O(L) where L = length of the search prefix.
- Much faster than linear search O(N) for large medicine lists.

Example tree for ["Paracetamol", "Panadol"]:
root -> p -> a -> r -> a -> c -> e -> t -> a -> m -> o -> l (end)
          -> n -> a -> d -> o -> l (end)
"""


class TrieNode:
    """Represents one character node in the Trie tree."""

    def __init__(self):
        # Dictionary mapping each character to its child node
        self.children = {}
        # True if a complete medicine name ends at this node
        self.is_end = False
        # Store extra medicine info at the end node (category, etc.)
        self.medicine_info = None


class Trie:
    """
    Prefix Tree for instant medicine name autocomplete.

    Usage:
        trie = Trie()
        trie.insert("Paracetamol", {"category": "Painkiller"})
        results = trie.search_prefix("para")
        # -> [{"name": "Paracetamol", "category": "Painkiller"}]
    """

    def __init__(self):
        self.root = TrieNode()
        self.total_medicines = 0

    def insert(self, medicine_name: str, info: dict = None):
        """
        Insert a medicine name into the Trie.

        Args:
            medicine_name: Name of the medicine (e.g., "Paracetamol")
            info: Optional dict with extra details (category, description)
        """
        node = self.root
        # Walk through each character, creating nodes as needed
        for char in medicine_name.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        # Mark the last character as the end of a word
        node.is_end = True
        node.medicine_info = info or {"name": medicine_name}
        self.total_medicines += 1

    def search_prefix(self, prefix: str, max_results: int = 10) -> list:
        """
        Find all medicine names that START WITH the given prefix.
        This powers the autocomplete feature.

        Args:
            prefix: The typed text (e.g., "para")
            max_results: Maximum suggestions to return

        Returns:
            List of dicts: [{"name": "Paracetamol", "category": "..."}, ...]
        """
        prefix = prefix.lower().strip()
        if not prefix:
            return []

        # Step 1: Navigate to the node matching the last char of prefix
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []  # No medicine starts with this prefix
            node = node.children[char]

        # Step 2: From that node, collect all complete words below it
        results = []
        self._collect_all_words(node, prefix, results, max_results)
        return results

    def _collect_all_words(self, node: TrieNode, current_word: str,
                           results: list, max_results: int):
        """
        Depth-first search from a node to find all complete medicine names.
        Appends found medicines to the results list.
        """
        if len(results) >= max_results:
            return  # Stop once we have enough suggestions

        if node.is_end:
            # Found a complete medicine name - add it to results
            entry = dict(node.medicine_info) if node.medicine_info else {}
            entry["name"] = current_word.title()  # Proper capitalization
            results.append(entry)

        # Recursively explore all child characters (alphabetical order)
        for char in sorted(node.children.keys()):
            self._collect_all_words(
                node.children[char],
                current_word + char,
                results,
                max_results
            )

    def exact_search(self, medicine_name: str) -> bool:
        """Check if an exact medicine name exists in the Trie."""
        node = self.root
        for char in medicine_name.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def get_all_medicines(self) -> list:
        """Return every medicine stored in the Trie (used for initialization)."""
        results = []
        self._collect_all_words(self.root, "", results, max_results=9999)
        return results

    def delete(self, medicine_name: str) -> bool:
        """Remove a medicine from the Trie. Returns True if it existed."""
        return self._delete_recursive(self.root, medicine_name.lower(), 0)

    def _delete_recursive(self, node: TrieNode, word: str, depth: int) -> bool:
        """Helper for deletion - returns True if the node can be removed."""
        if depth == len(word):
            if not node.is_end:
                return False  # Word doesn't exist
            node.is_end = False
            self.total_medicines -= 1
            return len(node.children) == 0  # Delete node if it's a leaf

        char = word[depth]
        if char not in node.children:
            return False

        should_delete_child = self._delete_recursive(
            node.children[char], word, depth + 1
        )

        if should_delete_child:
            del node.children[char]
            return len(node.children) == 0 and not node.is_end

        return False


# ---------------------------------------------------------------------------
# Singleton Pattern - One trie instance shared across all Flask requests
# ---------------------------------------------------------------------------

_global_trie = None


def get_trie() -> Trie:
    """Get (or create) the global Trie instance."""
    global _global_trie
    if _global_trie is None:
        _global_trie = Trie()
    return _global_trie


def build_trie_from_db(medicines: list) -> Trie:
    """
    Build the Trie from database records. Called at Flask app startup.

    Args:
        medicines: List of dicts from DB, each with 'medicine_name' and 'category'

    Returns:
        Populated Trie ready for searching
    """
    global _global_trie
    _global_trie = Trie()

    for med in medicines:
        _global_trie.insert(
            med["medicine_name"],
            {
                "name": med["medicine_name"],
                "category": med.get("category", "General"),
                "description": med.get("description", ""),
            }
        )

    print(f"[Trie] Built with {_global_trie.total_medicines} medicines.")
    return _global_trie
