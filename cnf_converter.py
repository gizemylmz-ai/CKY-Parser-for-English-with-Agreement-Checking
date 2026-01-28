"""
Context-Free Grammar to Chomsky Normal Form Converter

This module converts a given Context-Free Grammar (CFG) into Chomsky Normal Form (CNF).

CNF Requirements:
1. All rules must be in one of these forms:
   - A → BC (where A, B, C are non-terminals)
   - A → a (where A is a non-terminal and a is a terminal)
   - S → ε (only if S is the start symbol and doesn't appear on RHS)

Conversion Steps:
1. Add a new start symbol
2. Eliminate ε-productions
3. Eliminate unit productions (A → B)
4. Replace terminals in mixed rules
5. Break down rules with more than 2 symbols on RHS
"""

from collections import defaultdict
import string


class CFGtoCNFConverter:
    def __init__(self):
        self.grammar = defaultdict(list)  # Non-terminal -> list of productions
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = None
        self.new_var_counter = 0
        
    def parse_grammar(self, grammar_rules: dict, start_symbol: str = 'S'):
        """
        Parse grammar rules from a dictionary.
        
        Args:
            grammar_rules: Dictionary where keys are non-terminals and values are 
                          lists of productions. Each production should be a LIST of symbols.
            start_symbol: The start symbol of the grammar (defaults to 'S')
        
        Example:
            grammar_rules = {
                'S': [['NP', 'VP']],
                'NP': [['Det', 'N'], ['N']],
                'VP': [['V', 'NP'], ['V']],
                'Det': [['the'], ['a']],
                'N': [['cat'], ['dog']],
                'V': [['chases'], ['sees']]
            }
            
            # For epsilon productions, use ['ε'] or ['epsilon']
            # Single terminal: [['word']]
        """
        self.grammar = defaultdict(list)
        self.non_terminals = set()
        self.terminals = set()
        
        # First pass: collect all non-terminals (keys of the grammar)
        for non_terminal in grammar_rules.keys():
            self.non_terminals.add(non_terminal)
        
        # Second pass: parse productions
        for non_terminal, productions in grammar_rules.items():
            for prod in productions:
                if isinstance(prod, list):
                    # Production is already a list of symbols
                    # Handle epsilon
                    if prod == ['ε'] or prod == ['epsilon']:
                        self.grammar[non_terminal].append(['ε'])
                    else:
                        self.grammar[non_terminal].append(prod)
                elif isinstance(prod, str):
                    # Single symbol as string (backward compatibility)
                    if prod == 'ε' or prod.lower() == 'epsilon':
                        self.grammar[non_terminal].append(['ε'])
                    else:
                        self.grammar[non_terminal].append([prod])
        
        # Identify terminals (symbols that are not non-terminals and not ε)
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                for symbol in prod:
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
        
        # Set start symbol
        self.start_symbol = start_symbol if start_symbol in self.non_terminals else 'S'
        
    def parse_grammar_from_string(self, grammar_string: str):
        """
        Parse grammar from a string format.
        
        Format: Each line is "NonTerminal -> production1 | production2 | ..."
        Symbols in productions should be SPACE-SEPARATED.
        Use 'ε' or 'epsilon' for empty productions.
        
        Example:
            S -> NP VP | VP
            NP -> Det N | N
            VP -> V NP | V
            Det -> the | a
            N -> cat | dog
            V -> sees | chases
        """
        grammar_rules = {}
        lines = grammar_string.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or '->' not in line:
                continue
                
            parts = line.split('->')
            non_terminal = parts[0].strip()
            raw_productions = [p.strip() for p in parts[1].split('|')]
            
            productions = []
            for prod in raw_productions:
                if prod.lower() == 'epsilon' or prod == 'ε':
                    productions.append(['ε'])
                else:
                    # Split on whitespace to get individual symbols
                    symbols = prod.split()
                    productions.append(symbols)
            
            grammar_rules[non_terminal] = productions
            
        self.parse_grammar(grammar_rules)
        
    def _generate_new_variable(self, prefix='X'):
        """Generate a new unique non-terminal variable."""
        while True:
            new_var = f"{prefix}{self.new_var_counter}"
            self.new_var_counter += 1
            if new_var not in self.non_terminals:
                self.non_terminals.add(new_var)
                return new_var
    
    def _start_symbol_on_rhs(self):
        """Check if the start symbol appears on the RHS of any production."""
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if self.start_symbol in prod:
                    return True
        return False
    
    def _step1_add_new_start_symbol(self):
        """
        Step 1: Add a new start symbol S0 -> S
        Only if the start symbol appears on the RHS of any rule.
        """
        if self._start_symbol_on_rhs():
            new_start = self._generate_new_variable('S')
            self.grammar[new_start] = [[self.start_symbol]]
            self.start_symbol = new_start
            print(f"  (S0 added because '{self.start_symbol}' appears on RHS)")
        else:
            print(f"  (S0 not needed - '{self.start_symbol}' doesn't appear on RHS)")
        
    def _find_nullable_variables(self):
        """Find all non-terminals that can derive ε (nullable variables)."""
        nullable = set()
        
        # Initial pass: find direct ε-productions
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if prod == ['ε']:
                    nullable.add(non_terminal)
        
        # Fixed-point iteration
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.grammar.items():
                if non_terminal in nullable:
                    continue
                for prod in productions:
                    # If all symbols in production are nullable
                    if all(symbol in nullable for symbol in prod):
                        nullable.add(non_terminal)
                        changed = True
                        break
        
        return nullable
    
    def _step2_eliminate_epsilon_productions(self):
        """
        Step 2: Eliminate ε-productions.
        For each nullable variable, add new productions with that variable removed.
        """
        nullable = self._find_nullable_variables()
        
        new_grammar = defaultdict(list)
        
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if prod == ['ε']:
                    continue  # Skip ε-productions
                
                # Find all positions of nullable variables
                nullable_positions = [i for i, symbol in enumerate(prod) if symbol in nullable]
                
                # Generate all subsets of nullable positions
                from itertools import combinations
                for r in range(len(nullable_positions) + 1):
                    for positions_to_remove in combinations(nullable_positions, r):
                        new_prod = [symbol for i, symbol in enumerate(prod) 
                                   if i not in positions_to_remove]
                        
                        if new_prod and new_prod not in new_grammar[non_terminal]:
                            new_grammar[non_terminal].append(new_prod)
        
        # If start symbol is nullable, add S -> ε
        if self.start_symbol in nullable:
            new_grammar[self.start_symbol].append(['ε'])
        
        self.grammar = new_grammar
        
    def _step3_eliminate_unit_productions(self):
        """
        Step 3: Eliminate unit productions (A -> B where B is a non-terminal).
        """
        # Find unit pairs using closure
        unit_pairs = set()
        
        # Initialize with identity pairs
        for nt in self.non_terminals:
            unit_pairs.add((nt, nt))
        
        # Find direct unit productions
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if len(prod) == 1 and prod[0] in self.non_terminals:
                    unit_pairs.add((non_terminal, prod[0]))
        
        # Compute closure
        changed = True
        while changed:
            changed = False
            new_pairs = set()
            for (a, b) in unit_pairs:
                for (c, d) in unit_pairs:
                    if b == c and (a, d) not in unit_pairs:
                        new_pairs.add((a, d))
                        changed = True
            unit_pairs.update(new_pairs)
        
        # Build new grammar
        new_grammar = defaultdict(list)
        
        for (a, b) in unit_pairs:
            if b in self.grammar:
                for prod in self.grammar[b]:
                    # Skip unit productions
                    if not (len(prod) == 1 and prod[0] in self.non_terminals):
                        if prod not in new_grammar[a]:
                            new_grammar[a].append(prod)
        
        self.grammar = new_grammar
        
    def _step4_replace_terminals_in_mixed_rules(self):
        """
        Step 4: Replace terminals in rules with more than one symbol.
        For each terminal 'a' appearing in mixed rules, create a new rule Ta -> a.
        """
        terminal_vars = {}  # Maps terminal to its new non-terminal
        new_grammar = defaultdict(list)
        
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if len(prod) == 1:
                    # Single symbol - keep as is
                    if prod not in new_grammar[non_terminal]:
                        new_grammar[non_terminal].append(prod)
                else:
                    # Multiple symbols - replace terminals
                    new_prod = []
                    for symbol in prod:
                        if symbol in self.terminals:
                            if symbol not in terminal_vars:
                                new_var = self._generate_new_variable('T')
                                terminal_vars[symbol] = new_var
                                new_grammar[new_var] = [[symbol]]
                            new_prod.append(terminal_vars[symbol])
                        else:
                            new_prod.append(symbol)
                    
                    if new_prod not in new_grammar[non_terminal]:
                        new_grammar[non_terminal].append(new_prod)
        
        self.grammar = new_grammar
        
    def _step5_break_long_productions(self):
        """
        Step 5: Break down productions with more than 2 symbols on RHS.
        A -> B1 B2 B3 ... Bn becomes:
        A -> B1 C1
        C1 -> B2 C2
        ...
        Cn-2 -> Bn-1 Bn
        """
        new_grammar = defaultdict(list)
        
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                if len(prod) <= 2:
                    if prod not in new_grammar[non_terminal]:
                        new_grammar[non_terminal].append(prod)
                else:
                    # Break down long production
                    current_nt = non_terminal
                    for i in range(len(prod) - 2):
                        new_var = self._generate_new_variable('Y')
                        new_grammar[current_nt].append([prod[i], new_var])
                        current_nt = new_var
                    # Last two symbols
                    new_grammar[current_nt].append([prod[-2], prod[-1]])
        
        self.grammar = new_grammar
        
    def convert_to_cnf(self) -> dict:
        """
        Convert the grammar to Chomsky Normal Form.
        
        Returns:
            Dictionary representing the CNF grammar
        """
        print("Original Grammar:")
        self.print_grammar()
        print()
        
        print("Step 1: Adding new start symbol...")
        self._step1_add_new_start_symbol()
        self.print_grammar()
        print()
        
        print("Step 2: Eliminating ε-productions...")
        self._step2_eliminate_epsilon_productions()
        self.print_grammar()
        print()
        
        print("Step 3: Eliminating unit productions...")
        self._step3_eliminate_unit_productions()
        self.print_grammar()
        print()
        
        print("Step 4: Replacing terminals in mixed rules...")
        self._step4_replace_terminals_in_mixed_rules()
        self.print_grammar()
        print()
        
        print("Step 5: Breaking long productions...")
        self._step5_break_long_productions()
        self.print_grammar()
        print()
        
        return dict(self.grammar)
    
    def print_grammar(self):
        """Print the current grammar in a readable format."""
        for non_terminal in sorted(self.grammar.keys()):
            productions = self.grammar[non_terminal]
            prod_strs = [' '.join(prod) for prod in productions]
            print(f"  {non_terminal} -> {' | '.join(prod_strs)}")
            
    def get_cnf_grammar(self) -> dict:
        """Return the current grammar as a dictionary."""
        return {nt: [''.join(prod) for prod in prods] 
                for nt, prods in self.grammar.items()}
    
    def is_valid_cnf(self) -> bool:
        """Check if the current grammar is in valid CNF."""
        for non_terminal, productions in self.grammar.items():
            for prod in productions:
                # Check for ε production (only allowed for start symbol)
                if prod == ['ε']:
                    if non_terminal != self.start_symbol:
                        return False
                    # Check start symbol doesn't appear on RHS
                    for nt, prods in self.grammar.items():
                        for p in prods:
                            if self.start_symbol in p:
                                return False
                # Check for single terminal
                elif len(prod) == 1:
                    if prod[0] not in self.terminals:
                        return False
                # Check for two non-terminals
                elif len(prod) == 2:
                    if prod[0] not in self.non_terminals or prod[1] not in self.non_terminals:
                        return False
                else:
                    return False
        return True


def main():
    """Demonstrate the CNF converter with example grammars."""
    
    print("=" * 60)
    print("Example 1: Simple NLP Grammar")
    print("=" * 60)
    
    converter = CFGtoCNFConverter()
    
    # Define a sample NLP grammar with multi-character symbols
    grammar1 = {
        'S': [['NP', 'VP']],
        'NP': [['Det', 'N'], ['N']],
        'VP': [['V', 'NP'], ['V']],
        'Det': [['the'], ['a']],
        'N': [['cat'], ['dog'], ['mouse']],
        'V': [['sees'], ['chases']]
    }
    
    converter.parse_grammar(grammar1)
    cnf_grammar = converter.convert_to_cnf()
    
    print("Final CNF Grammar:")
    print("-" * 40)
    converter.print_grammar()
    print(f"\nIs valid CNF: {converter.is_valid_cnf()}")
    
    print("\n" + "=" * 60)
    print("Example 2: Grammar with Epsilon and Unit Productions")
    print("=" * 60)
    
    converter2 = CFGtoCNFConverter()
    
    grammar2 = {
        'S': [['NP', 'VP']],
        'NP': [['Det', 'Nom'], ['Nom']],
        'Nom': [['Adj', 'Nom'], ['N']],
        'VP': [['V', 'NP'], ['V', 'S'], ['V']],
        'Det': [['the'], ['a'], ['ε']],
        'Adj': [['big'], ['small']],
        'N': [['cat'], ['dog']],
        'V': [['sees'], ['thinks']]
    }
    
    converter2.parse_grammar(grammar2)
    converter2.convert_to_cnf()
    
    print("Final CNF Grammar:")
    print("-" * 40)
    converter2.print_grammar()
    print(f"\nIs valid CNF: {converter2.is_valid_cnf()}")
    
    print("\n" + "=" * 60)
    print("Example 3: Parsing from String Format")
    print("=" * 60)
    
    converter3 = CFGtoCNFConverter()
    
    # Note: Symbols must be space-separated in string format
    grammar_string = """
    S -> NP VP
    NP -> Det N | N
    VP -> V NP | V PP | V
    PP -> P NP
    Det -> the | a
    N -> man | park | dog
    V -> saw | walked
    P -> in | with
    """
    
    converter3.parse_grammar_from_string(grammar_string)
    converter3.convert_to_cnf()
    
    print("Final CNF Grammar:")
    print("-" * 40)
    converter3.print_grammar()
    print(f"\nIs valid CNF: {converter3.is_valid_cnf()}")
    
    print("\n" + "=" * 60)
    print("Example 4: Non-Binary Grammar (3+ symbols on RHS)")
    print("=" * 60)
    
    converter4 = CFGtoCNFConverter()
    
    # Grammar with non-binary productions (3, 4 symbols on RHS)
    grammar4 = {
        'S': [['NP', 'VP', 'PP']],           # 3 symbols
        'NP': [['Det', 'Adj', 'N']],          # 3 symbols
        'VP': [['V', 'NP', 'PP', 'Adv']],     # 4 symbols!
        'PP': [['P', 'Det', 'Adj', 'N']],     # 4 symbols!
        'Det': [['the'], ['a']],
        'Adj': [['big'], ['small']],
        'N': [['cat'], ['dog']],
        'V': [['saw']],
        'P': [['in'], ['on']],
        'Adv': [['quickly']]
    }
    
    converter4.parse_grammar(grammar4)
    converter4.convert_to_cnf()
    
    print("Final CNF Grammar:")
    print("-" * 40)
    converter4.print_grammar()
    print(f"\nIs valid CNF: {converter4.is_valid_cnf()}")


if __name__ == "__main__":
    """Convert English grammar to CNF and save."""
    import json
    from pathlib import Path
    
    script_dir = Path(__file__).parent
    input_file = script_dir / "data" / "english_grammar.json"
    output_file = script_dir / "data" / "english_grammar_cnf.json"
    
    print("=" * 60)
    print("Converting English Grammar to CNF")
    print("=" * 60)
    
    # Load original grammar
    if not input_file.exists():
        print(f"Error: {input_file} not found. Run english_cfg.py first.")
        exit(1)
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    original_grammar = data['rules']
    start_symbol = data['start_symbol']
    
    print(f"\nLoaded grammar from {input_file}")
    print(f"Start symbol: {start_symbol}")
    print(f"Original rules: {sum(len(prods) for prods in original_grammar.values())}")
    
    # Convert to CNF
    converter = CFGtoCNFConverter()
    converter.parse_grammar(original_grammar, start_symbol)
    cnf_grammar = converter.convert_to_cnf()
    
    # Deduplicate CNF rules
    print("\n" + "=" * 60)
    print("Deduplicating CNF rules...")
    print("=" * 60)
    
    deduplicated = {}
    total_removed = 0
    for nt, prods in cnf_grammar.items():
        seen = set()
        unique_prods = []
        for prod in prods:
            prod_tuple = tuple(prod)
            if prod_tuple not in seen:
                seen.add(prod_tuple)
                unique_prods.append(prod)
            else:
                total_removed += 1
        deduplicated[nt] = unique_prods
    
    print(f"Removed {total_removed} duplicate rules")
    print(f"Final CNF rules: {sum(len(prods) for prods in deduplicated.values())}")
    
    # Save CNF grammar
    cnf_data = {
        'start_symbol': converter.start_symbol,
        'rules': deduplicated,
        'is_cnf': True
    }
    
    with open(output_file, 'w') as f:
        json.dump(cnf_data, f, indent=2)
    
    print(f"\nCNF Grammar saved to {output_file}")
    print("=" * 60)

