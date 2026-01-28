"""
Parse Tree Converter

This module converts parse trees from CNF (Chomsky Normal Form) back to the 
original CFG structure. It removes auxiliary non-terminals (like Y0, Y1, T0, T1)
that were introduced during CNF conversion.

This is the reverse operation of CNF conversion - also known as "de-binarization".
"""

from typing import List, Tuple, Dict, Set, Any, Optional


class ParseTreeConverter:
    def __init__(self):
        # Set of auxiliary non-terminals to flatten/remove
        self.auxiliary_prefixes = {'Y', 'T', 'S0'}  # Default prefixes from CNF converter
        self.auxiliary_nts = set()
        
        # Original grammar (if provided, for validation)
        self.original_grammar = None
        self.original_non_terminals = set()
        
    def set_auxiliary_prefixes(self, prefixes: List[str]):
        """
        Set the prefixes used for auxiliary non-terminals.
        
        Args:
            prefixes: List of prefixes (e.g., ['Y', 'T', 'X'])
        """
        self.auxiliary_prefixes = set(prefixes)
        
    def load_original_grammar(self, grammar: dict):
        """
        Load the original grammar to identify which non-terminals are auxiliary.
        
        Args:
            grammar: The original CFG grammar (before CNF conversion)
        """
        self.original_grammar = grammar
        self.original_non_terminals = set(grammar.keys())
        
    def set_auxiliary_nts(self, auxiliary_nts: Set[str]):
        """
        Explicitly set which non-terminals are auxiliary.
        
        Args:
            auxiliary_nts: Set of auxiliary non-terminal names
        """
        self.auxiliary_nts = auxiliary_nts
        
    def is_auxiliary(self, nt: str) -> bool:
        """
        Check if a non-terminal is auxiliary (should be flattened).
        
        Args:
            nt: Non-terminal symbol
            
        Returns:
            True if auxiliary, False otherwise
        """
        # If explicitly set
        if self.auxiliary_nts and nt in self.auxiliary_nts:
            return True
            
        # If we know the original grammar, anything not in it is auxiliary
        if self.original_non_terminals and nt not in self.original_non_terminals:
            return True
            
        # Check by prefix pattern (Y0, Y1, T0, T1, etc.)
        for prefix in self.auxiliary_prefixes:
            if nt.startswith(prefix) and (len(nt) == len(prefix) or nt[len(prefix):].isdigit()):
                return True
                
        return False
    
    def convert(self, tree: Tuple) -> Tuple:
        """
        Convert a CNF parse tree back to original CFG structure.
        
        This flattens auxiliary non-terminals, effectively reconstructing
        the original n-ary branching structure from the binary CNF tree.
        
        Args:
            tree: Parse tree from CKY parser
                  Format: (NT, child1, child2) or (NT, terminal)
                  
        Returns:
            Converted parse tree with auxiliary NTs removed
        """
        if tree is None:
            return None
            
        return self._convert_node(tree)
    
    def _convert_node(self, node: Tuple) -> Tuple:
        """Recursively convert a node and its children."""
        if len(node) == 2 and isinstance(node[1], str):
            # Leaf node: (NT, terminal)
            return node
            
        # Internal node: (NT, left_child, right_child)
        nt = node[0]
        children = list(node[1:])
        
        # Recursively convert children first
        converted_children = []
        for child in children:
            converted_child = self._convert_node(child)
            
            # If the child is an auxiliary NT, flatten its children
            if isinstance(converted_child, tuple) and len(converted_child) > 1:
                child_nt = converted_child[0]
                if self.is_auxiliary(child_nt):
                    # Flatten: add the auxiliary's children directly
                    converted_children.extend(converted_child[1:])
                else:
                    converted_children.append(converted_child)
            else:
                converted_children.append(converted_child)
        
        # If current node is auxiliary, return just the children (will be flattened above)
        # But if it's the root, we keep it
        return (nt,) + tuple(converted_children)
    
    def convert_all(self, trees: List[Tuple]) -> List[Tuple]:
        """
        Convert multiple parse trees.
        
        Args:
            trees: List of parse trees from CKY parser
            
        Returns:
            List of converted parse trees
        """
        return [self.convert(tree) for tree in trees]
    
    def format_tree(self, tree: Tuple, indent: int = 0) -> str:
        """
        Format a parse tree as a string with indentation.
        
        Args:
            tree: Parse tree
            indent: Current indentation level
            
        Returns:
            Formatted string representation
        """
        if tree is None:
            return ""
        
        # Handle string terminals directly (e.g., 'VBD', 'NN')
        if isinstance(tree, str):
            return "  " * indent + tree
            
        if len(tree) == 2 and isinstance(tree[1], str):
            # Leaf node: (NT, terminal) like ('NP', 'PRP')
            return "  " * indent + f"({tree[0]} {tree[1]})"
        else:
            # Internal node with children
            result = "  " * indent + f"({tree[0]}\n"
            for child in tree[1:]:
                result += self.format_tree(child, indent + 1) + "\n"
            result = result.rstrip() + ")"
            return result
    
    def format_tree_bracket(self, tree: Tuple) -> str:
        """
        Format a parse tree in bracket notation (one line).
        
        Args:
            tree: Parse tree
            
        Returns:
            Bracket notation string
        """
        if tree is None:
            return ""
        
        # Handle string terminals directly
        if isinstance(tree, str):
            return tree
            
        if len(tree) == 2 and isinstance(tree[1], str):
            return f"({tree[0]} {tree[1]})"
        else:
            children = " ".join(self.format_tree_bracket(child) for child in tree[1:])
            return f"({tree[0]} {children})"
    
    def get_tree_depth(self, tree: Tuple) -> int:
        """Calculate the depth of a parse tree."""
        if tree is None:
            return 0
        if len(tree) == 2 and isinstance(tree[1], str):
            return 1
        return 1 + max(self.get_tree_depth(child) for child in tree[1:])
    
    def count_nodes(self, tree: Tuple) -> Dict[str, int]:
        """
        Count the number of nodes by type in the tree.
        
        Returns:
            Dictionary with 'total', 'internal', 'leaf' counts
        """
        if tree is None:
            return {'total': 0, 'internal': 0, 'leaf': 0}
            
        if len(tree) == 2 and isinstance(tree[1], str):
            return {'total': 1, 'internal': 0, 'leaf': 1}
            
        counts = {'total': 1, 'internal': 1, 'leaf': 0}
        for child in tree[1:]:
            child_counts = self.count_nodes(child)
            counts['total'] += child_counts['total']
            counts['internal'] += child_counts['internal']
            counts['leaf'] += child_counts['leaf']
        return counts
    
    def extract_constituents(self, tree: Tuple, sentence: List[str] = None) -> List[Tuple[str, int, int, str]]:
        """
        Extract all constituents (phrases) from the parse tree.
        
        Args:
            tree: Parse tree
            sentence: Optional list of words for span text
            
        Returns:
            List of (label, start, end, text) tuples
        """
        constituents = []
        self._extract_constituents_helper(tree, 0, constituents, sentence)
        return constituents
    
    def _extract_constituents_helper(self, node: Tuple, start: int, 
                                      constituents: List, sentence: List[str] = None) -> int:
        """Helper for constituent extraction."""
        if len(node) == 2 and isinstance(node[1], str):
            # Leaf node
            end = start + 1
            text = sentence[start] if sentence and start < len(sentence) else node[1]
            constituents.append((node[0], start, end, text))
            return end
            
        # Internal node
        current_pos = start
        child_texts = []
        
        for child in node[1:]:
            end_pos = self._extract_constituents_helper(child, current_pos, constituents, sentence)
            if sentence:
                child_texts.extend(sentence[current_pos:end_pos])
            current_pos = end_pos
        
        text = " ".join(child_texts) if child_texts else ""
        constituents.append((node[0], start, current_pos, text))
        return current_pos


def main():
    """Demonstrate the parse tree converter."""
    
    print("=" * 60)
    print("Parse Tree Converter Demo")
    print("=" * 60)
    
    # Import the other modules
    from cnf_converter import CFGtoCNFConverter
    from cky_parser import CKYParser
    
    # Define original grammar with non-binary rules
    original_grammar = {
        'S': [['NP', 'VP']],
        'NP': [['Det', 'Adj', 'N'], ['Det', 'N'], ['N']],  # Non-binary!
        'VP': [['V', 'NP'], ['V']],
        'Det': [['the'], ['a']],
        'Adj': [['big'], ['small'], ['lazy']],
        'N': [['cat'], ['dog'], ['mouse']],
        'V': [['sees'], ['chases']]
    }
    
    print("\n1. Original Grammar (non-binary):")
    print("-" * 40)
    for nt, prods in original_grammar.items():
        prod_strs = [' '.join(p) for p in prods]
        print(f"  {nt} -> {' | '.join(prod_strs)}")
    
    # Convert to CNF
    print("\n2. Converting to CNF...")
    print("-" * 40)
    converter = CFGtoCNFConverter()
    converter.parse_grammar(original_grammar)
    converter.convert_to_cnf()
    
    # Parse a sentence
    print("\n3. Parsing sentence with CKY...")
    print("-" * 40)
    parser = CKYParser()
    parser.load_grammar_from_converter(converter)
    
    sentence = ['the', 'big', 'cat', 'sees', 'the', 'small', 'dog']
    print(f"Sentence: {' '.join(sentence)}")
    
    success, trees = parser.parse(sentence)
    
    if success:
        print(f"\n✓ Parsed successfully!")
        
        # Show CNF parse tree
        print("\n4. CNF Parse Tree (with auxiliary nodes Y0, etc.):")
        print("-" * 40)
        print(parser.format_tree(trees[0]))
        
        # Convert back to original structure
        print("\n5. Converting back to original CFG structure...")
        print("-" * 40)
        
        tree_converter = ParseTreeConverter()
        tree_converter.load_original_grammar(original_grammar)
        
        original_tree = tree_converter.convert(trees[0])
        
        print("Reconstructed Parse Tree (auxiliary nodes removed):")
        print(tree_converter.format_tree(original_tree))
        
        # Show bracket notation
        print("\n6. Bracket Notation:")
        print("-" * 40)
        print(f"CNF:      {parser.format_tree_bracket(trees[0])}")
        print(f"Original: {tree_converter.format_tree_bracket(original_tree)}")
        
        # Extract constituents
        print("\n7. Extracted Constituents:")
        print("-" * 40)
        constituents = tree_converter.extract_constituents(original_tree, sentence)
        for label, start, end, text in sorted(constituents, key=lambda x: (x[1], -x[2])):
            print(f"  {label:6} [{start}:{end}] = '{text}'")
        
        # Statistics
        print("\n8. Tree Statistics:")
        print("-" * 40)
        cnf_counts = tree_converter.count_nodes(trees[0])
        orig_counts = tree_converter.count_nodes(original_tree)
        print(f"  CNF tree:      {cnf_counts['total']} nodes ({cnf_counts['internal']} internal, {cnf_counts['leaf']} leaves)")
        print(f"  Original tree: {orig_counts['total']} nodes ({orig_counts['internal']} internal, {orig_counts['leaf']} leaves)")
        print(f"  Nodes removed: {cnf_counts['total'] - orig_counts['total']}")
    else:
        print("✗ Failed to parse")


if __name__ == "__main__":
    main()
