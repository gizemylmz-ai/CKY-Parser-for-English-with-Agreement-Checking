"""
CKY (Cocke-Kasami-Younger) Parser

A generic CKY parser that works with ANY grammar in Chomsky Normal Form (CNF).
This parser can be used with the output of cnf_converter.py.

The CKY algorithm is a bottom-up chart parsing algorithm with O(n³) time complexity,
where n is the length of the input sentence.
"""

from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional


class CKYParser:
    def __init__(self):
        self.grammar = {}  # Non-terminal -> list of productions
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = 'S'
        
        # Reverse lookup: RHS -> list of LHS non-terminals
        self.terminal_rules = defaultdict(list)    # terminal -> [NT1, NT2, ...]
        self.binary_rules = defaultdict(list)      # (NT1, NT2) -> [A, B, ...]
        
    def load_grammar(self, grammar: dict, start_symbol: str = 'S'):
        """
        Load a CNF grammar.
        
        Args:
            grammar: Dictionary where keys are non-terminals and values are 
                    lists of productions. Each production is a list of symbols.
            start_symbol: The start symbol of the grammar
        
        Example:
            grammar = {
                'S': [['NP', 'VP']],
                'NP': [['Det', 'N'], ['cat'], ['dog']],
                'VP': [['V', 'NP'], ['sees']],
                'Det': [['the'], ['a']],
                'N': [['cat'], ['dog']],
                'V': [['sees'], ['chases']]
            }
        """
        self.grammar = grammar
        self.start_symbol = start_symbol
        
        # Identify non-terminals and build reverse lookup tables
        self.non_terminals = set(grammar.keys())
        
        for nt, productions in grammar.items():
            for prod in productions:
                if len(prod) == 1:
                    # Terminal rule: A -> a
                    terminal = prod[0]
                    self.terminals.add(terminal)
                    self.terminal_rules[terminal].append(nt)
                elif len(prod) == 2:
                    # Binary rule: A -> BC
                    b, c = prod[0], prod[1]
                    self.binary_rules[(b, c)].append(nt)
        
    def load_grammar_from_converter(self, converter):
        """
        Load grammar directly from a CFGtoCNFConverter instance.
        
        Args:
            converter: A CFGtoCNFConverter instance after convert_to_cnf() has been called
        """
        # Convert internal format to simple format
        grammar = {}
        for nt, productions in converter.grammar.items():
            grammar[nt] = [list(prod) for prod in productions]
        
        self.load_grammar(grammar, converter.start_symbol)
        
    def parse(self, sentence: List[str], pos_constraints: List[str] = None, verbose: bool = False) -> Tuple[bool, Optional[List]]:
        """
        Parse a sentence using the CKY algorithm.
        
        Args:
            sentence: List of tokens (words) to parse
            pos_constraints: Optional list of POS tags for each word. If provided, 
                             these tags will be used to initialize the diagonal,
                             bypassing the lexical rules in the grammar.
            verbose: If True, print the chart after parsing
            
        Returns:
            Tuple of (success: bool, parse_trees: list or None)
        """
        n = len(sentence)
        if n == 0:
            return False, None
            
        if pos_constraints and len(pos_constraints) != n:
            return False, None
        
        # Initialize the chart
        chart = [[set() for _ in range(n)] for _ in range(n)]
        back = [[defaultdict(list) for _ in range(n)] for _ in range(n)]
        
        # Step 1: Fill diagonal
        if pos_constraints:
            # Manually fill with provided tags
            for i, (word, tag) in enumerate(zip(sentence, pos_constraints)):
                chart[i][i].add(tag)
                back[i][i][tag].append(('terminal', word))
                
                # ALSO add non-terminals that derive this tag in the CNF grammar (T_ nodes)
                for nt in self.terminal_rules.get(tag, []):
                    if nt not in chart[i][i]:
                        chart[i][i].add(nt)
                        # Point to the tag node itself at the same position
                        back[i][i][nt].append(('node', tag, i, i))
        else:
            # Fill using grammar terminal rules
            for i, word in enumerate(sentence):
                for nt in self.terminal_rules.get(word, []):
                    chart[i][i].add(nt)
                    back[i][i][nt].append(('terminal', word))
        
        # Step 2: Fill the chart bottom-up
        for span_length in range(2, n + 1):
            for i in range(n - span_length + 1):
                j = i + span_length - 1
                for k in range(i, j):
                    for b in chart[i][k]:
                        for c in chart[k + 1][j]:
                            for a in self.binary_rules.get((b, c), []):
                                chart[i][j].add(a)
                                back[i][j][a].append(('binary', b, c, k))
        
        if verbose:
            self._print_chart(chart, sentence)
        
        success = self.start_symbol in chart[0][n - 1]
        
        if success:
            trees = self._build_trees(back, 0, n - 1, self.start_symbol, sentence)
            return True, trees
        else:
            return False, None
    
    def _build_trees(self, back, i, j, nt, sentence, max_trees=10) -> List:
        """Recursively build parse trees from backpointers."""
        trees = []
        
        for entry in back[i][j].get(nt, [])[:max_trees]:
            if entry[0] == 'terminal':
                # Leaf node
                word = entry[1]
                trees.append((nt, word))
            elif entry[0] == 'node':
                # Unit-like node (e.g. T0 -> PRP)
                _, child_nt, ci, cj = entry
                child_trees = self._build_trees(back, ci, cj, child_nt, sentence, max_trees)
                for child in child_trees:
                    trees.append((nt, child))
            else:
                # Binary split
                _, b, c, k = entry
                left_trees = self._build_trees(back, i, k, b, sentence, max_trees)
                right_trees = self._build_trees(back, k + 1, j, c, sentence, max_trees)
                
                for left in left_trees[:max_trees]:
                    for right in right_trees[:max_trees]:
                        trees.append((nt, left, right))
                        if len(trees) >= max_trees:
                            return trees
        
        return trees
    
    def _print_chart(self, chart, sentence):
        """Print the CKY chart for debugging."""
        n = len(sentence)
        print("\nCKY Chart:")
        print("-" * 50)
        
        # Print header
        print("     ", end="")
        for i, word in enumerate(sentence):
            print(f"{word:^12}", end="")
        print()
        
        for i in range(n):
            print(f"{i:3}: ", end="")
            for j in range(n):
                if j < i:
                    print(f"{'':^12}", end="")
                else:
                    cell = chart[i][j]
                    cell_str = ",".join(sorted(cell)) if cell else "-"
                    if len(cell_str) > 10:
                        cell_str = cell_str[:9] + "…"
                    print(f"{cell_str:^12}", end="")
            print()
    
    def format_tree(self, tree, indent=0) -> str:
        """Format a parse tree as a string with indentation."""
        if len(tree) == 2 and isinstance(tree[1], str):
            # Leaf node
            return "  " * indent + f"({tree[0]} {tree[1]})"
        else:
            # Internal node
            result = "  " * indent + f"({tree[0]}\n"
            for child in tree[1:]:
                result += self.format_tree(child, indent + 1) + "\n"
            result = result.rstrip() + ")"
            return result
    
    def format_tree_bracket(self, tree) -> str:
        """Format a parse tree in bracket notation (one line)."""
        if len(tree) == 2 and isinstance(tree[1], str):
            return f"({tree[0]} {tree[1]})"
        else:
            children = " ".join(self.format_tree_bracket(child) for child in tree[1:])
            return f"({tree[0]} {children})"


def main():
    """Demonstrate the CKY parser with example grammars."""
    
    print("=" * 60)
    print("CKY Parser Demo")
    print("=" * 60)
    
    # Example 1: Simple grammar loaded directly
    print("\nExample 1: Simple NLP Grammar")
    print("-" * 40)
    
    parser = CKYParser()
    
    grammar = {
        'S': [['NP', 'VP']],
        'NP': [['Det', 'N'], ['the'], ['a'], ['cat'], ['dog']],
        'VP': [['V', 'NP'], ['sees'], ['chases']],
        'Det': [['the'], ['a']],
        'N': [['cat'], ['dog'], ['mouse']],
        'V': [['sees'], ['chases']]
    }
    
    parser.load_grammar(grammar, start_symbol='S')
    
    # Test sentences
    sentences = [
        ['the', 'cat', 'sees', 'the', 'dog'],
        ['a', 'dog', 'chases', 'the', 'mouse'],
        ['cat', 'sees', 'dog'],  # Without determiners
    ]
    
    for sentence in sentences:
        print(f"\nSentence: {' '.join(sentence)}")
        success, trees = parser.parse(sentence, verbose=False)
        
        if success:
            print(f"✓ Parsed successfully! ({len(trees)} parse tree(s))")
            if trees:
                print(f"Bracket notation: {parser.format_tree_bracket(trees[0])}")
        else:
            print("✗ Failed to parse")
    
    # Example 2: Using the CNF converter
    print("\n" + "=" * 60)
    print("Example 2: Using CNF Converter Output")
    print("-" * 40)
    
    from cnf_converter import CFGtoCNFConverter
    
    converter = CFGtoCNFConverter()
    
    # Define a grammar with non-binary rules
    grammar2 = {
        'S': [['NP', 'VP']],
        'NP': [['Det', 'Adj', 'N'], ['Det', 'N'], ['N']],
        'VP': [['V', 'NP'], ['V']],
        'Det': [['the'], ['a']],
        'Adj': [['big'], ['small'], ['lazy']],
        'N': [['cat'], ['dog'], ['fox']],
        'V': [['sees'], ['chases'], ['jumps']]
    }
    
    converter.parse_grammar(grammar2)
    print("Converting grammar to CNF...")
    converter.convert_to_cnf()
    
    print("\nLoading CNF grammar into parser...")
    parser2 = CKYParser()
    parser2.load_grammar_from_converter(converter)
    
    # Test with the CNF grammar
    test_sentences = [
        ['the', 'big', 'cat', 'sees', 'the', 'small', 'dog'],
        ['a', 'lazy', 'fox', 'jumps'],
        ['the', 'dog', 'chases', 'the', 'cat'],
    ]
    
    for sentence in test_sentences:
        print(f"\nSentence: {' '.join(sentence)}")
        success, trees = parser2.parse(sentence, verbose=False)
        
        if success:
            print(f"✓ Parsed successfully! ({len(trees)} parse tree(s))")
            if trees:
                print("\nParse tree:")
                print(parser2.format_tree(trees[0]))
        else:
            print("✗ Failed to parse")


if __name__ == "__main__":
    main()
