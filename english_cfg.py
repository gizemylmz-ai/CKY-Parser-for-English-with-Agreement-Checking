"""
English Context-Free Grammar (CFG) using Penn Treebank POS Tags

This module defines a comprehensive CFG for English that can parse:
- Declarative sentences (SVO order)
- Imperative sentences
- Yes/No questions
- Wh-questions

The grammar uses only Penn Treebank POS tags and is designed to work
with the CKY parser and CNF converter.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class EnglishCFG:
    """
    English Context-Free Grammar using Penn Treebank POS tags.
    
    POS Tag Reference:
    - NN: Noun, singular
    - NNS: Noun, plural
    - NNP: Proper noun, singular
    - NNPS: Proper noun, plural
    - VB: Verb, base form
    - VBD: Verb, past tense
    - VBP: Verb, non-3rd person singular present
    - VBZ: Verb, 3rd person singular present
    - VBG: Verb, gerund/present participle
    - VBN: Verb, past participle
    - DT: Determiner
    - JJ: Adjective
    - JJR: Adjective, comparative
    - JJS: Adjective, superlative
    - RB: Adverb
    - RBR: Adverb, comparative
    - RBS: Adverb, superlative
    - PRP: Personal pronoun
    - PRP$: Possessive pronoun
    - IN: Preposition
    - TO: "to"
    - CC: Coordinating conjunction
    - MD: Modal
    - WP: Wh-pronoun (who, what)
    - WDT: Wh-determiner (which)
    - WRB: Wh-adverb (when, where, why)
    - CD: Cardinal number
    - EX: Existential there
    - PDT: Predeterminer
    - POS: Possessive ending
    - RP: Particle
    - UH: Interjection
    """
    
    def __init__(self):
        self.grammar = {}
        self.start_symbol = 'S'
        self._build_grammar()
    
    def _build_grammar(self):
        """Build the complete CFG grammar."""
        
        # ========================================
        # SENTENCE LEVEL RULES
        # ========================================
        
        # S: Sentence (start symbol) - all sentence types directly here
        self.grammar['S'] = [
            # Declarative sentences (SVO/SVA)
            ['NP', 'VP'],               # "I bought a book", "I don't want anything"
            ['NP', 'VP', 'PP'],         # "I bought a book for my friend"
            ['NP', 'VP', 'RB'],         # "I bought a book yesterday"
            ['NP', 'VP', 'PP', 'RB'],   # "I bought a book for my friend yesterday"
            ['NP', 'VP', 'PP', 'NP'],   # "He jogged around the park every morning"
            ['NP', 'VP', 'NP'],         # "I saw that movie last week"
            
            # Imperative sentences
            ['VP'],                     # "Buy a book"
            ['VP', 'PP'],               # "Buy a book for me"
            ['RB', 'VP'],               # "Please buy a book"
            
            # Yes/No questions
            ['MD', 'NP', 'VP'],         # "Will you attend the meeting?"
            ['VBZ', 'NP', 'VP'],        # "Is he coming?"
            ['VBP', 'NP', 'VP'],
            ['VBD', 'NP', 'VP'],
            ['VBZ', 'NP', 'NP'],        # "Is he a teacher?"
            ['VBP', 'NP', 'NP'],
            ['VBD', 'NP', 'NP'],
            ['VBZ', 'NP', 'JJ'],        # "Is he happy?"
            ['VBZ', 'NP', 'RB', 'JJ'],
            ['VBP', 'NP', 'JJ'],
            ['VBD', 'NP', 'JJ'],
            
            # Wh-questions
            ['WRB', 'VBZ', 'NP', 'VP'],  # "When did you come here?"
            ['WRB', 'VBP', 'NP', 'VP'],
            ['WRB', 'VBD', 'NP', 'VP'],
            ['WRB', 'MD', 'NP', 'VP'],   # "When will you come?"
            ['WP', 'VBZ', 'NP', 'VP'],   # "What did you buy?"
            ['WP', 'VBP', 'NP', 'VP'],
            ['WP', 'VBD', 'NP', 'VP'],
            ['WP', 'MD', 'NP', 'VP'],
            ['WDT', 'NN', 'VBZ', 'NP', 'VP'],
            ['WDT', 'NN', 'VBP', 'NP', 'VP'],
            ['WDT', 'NN', 'VBD', 'NP', 'VP'],
            ['WDT', 'NNS', 'VBZ', 'NP', 'VP'],
            ['WP', 'VP'],               # "Who bought a book?"
            ['WDT', 'NN', 'VP'],
            ['WDT', 'NNS', 'VP'],
            ['WP', 'VBZ', 'VP'],        # "What is happening?"
            ['WP', 'VBP', 'VP'],
            ['WP', 'VBD', 'VP'],
            ['WRB', 'VBZ', 'NP', 'VP', 'RB'],  # "When did you come here lastly?"
            ['WRB', 'VBP', 'NP', 'VP', 'RB'],
            ['WRB', 'VBD', 'NP', 'VP', 'RB'],
            ['WRB', 'MD', 'NP', 'VP', 'RB'],
            
            # Imperative with negation (VB RB VP)
            ['VB', 'RB', 'VP'],         # "Do not listen"
            ['VBP', 'RB', 'VP'],
            
            # Interjection + imperative (Please...)
            ['UH', 'VP'],                   # "Please buy a book"
            ['UH', 'VP', 'PP'],             # "Please write your name on this paper"
            
            # ========================================
            # COORDINATION (S CC S)
            # ========================================
            ['S', 'CC', 'S'],               # "I read and he writes"
        ]
        
        # ========================================
        # PHRASE LEVEL RULES
        # ========================================
        
        # NP: Noun Phrase
        self.grammar['NP'] = [
            # Pronouns (simplest)
            ['PRP'],                # "I", "he", "they"
            
            # Proper nouns
            ['NNP'],                # "John"
            ['NNPS'],               # "Americans"
            ['NNP', 'NNP'],         # "John Smith"
            
            # Basic noun phrases
            ['NN'],                 # "water" (mass noun)
            ['NNS'],                # "books" (plural without determiner)
            ['DT', 'NN'],           # "the book"
            ['DT', 'NNS'],          # "the books"
            ['DT', 'NN', 'NN'],     # "the city center" (compound noun)
            
            # With adjectives
            ['DT', 'JJ', 'NN'],     # "the historical novel"
            ['DT', 'JJ', 'NNS'],    # "the historical novels"
            ['DT', 'RB', 'JJ', 'NN'],   # "the very big book"
            ['DT', 'RB', 'JJ', 'NNS'],
            ['DT', 'JJR', 'NN'],    # "the larger book"
            ['DT', 'JJR', 'NNS'],
            ['DT', 'JJS', 'NN'],    # "the biggest book"
            ['DT', 'JJS', 'NNS'],
            ['DT', 'RBS', 'JJ', 'NN'],  # "the most beautiful fruit"
            ['DT', 'RBS', 'JJ', 'NNS'],
            
            # Bare adjective + noun (no determiner)
            ['JJ', 'NN'],           # "historical novel"
            ['JJ', 'NNS'],          # "historical novels"
            ['RB', 'JJ', 'NN'],     # "very big book"
            ['RB', 'JJ', 'NNS'],
            ['JJR', 'NNS'],         # "fewer apples"
            ['JJS', 'NNS'],
            
            # Multiple adjectives
            ['DT', 'JJ', 'JJ', 'NN'],   # "the big red book"
            ['DT', 'JJ', 'JJ', 'NNS'],  # "the big red books"
            
            # With possessives
            ['PRP$', 'NN'],         # "my friend"
            ['PRP$', 'NNS'],        # "my friends"
            ['PRP$', 'JJ', 'NN'],   # "my best friend"
            ['PRP$', 'JJ', 'NNS'],  # "my best friends"
            
            # With cardinal numbers
            ['CD', 'NN'],           # "one book"
            ['CD', 'NNS'],          # "two books"
            ['CD', 'JJ', 'NNS'],    # "two historical novels"
            ['DT', 'CD', 'NNS'],    # "the two books"
            
            # Bare adjective + noun (no determiner)
            ['JJ', 'NN'],           # "historical novel"
            ['JJ', 'NNS'],          # "historical novels"
            ['RB', 'JJ', 'NN'],     # "very big book"
            ['RB', 'JJ', 'NNS'],
            ['JJR', 'NN'],
            ['JJR', 'NNS'],
            ['JJS', 'NN'],
            ['JJS', 'NNS'],
            ['RBS', 'JJ', 'NN'],
            
            # Comparative with 'than'
            ['NP', 'PP'],           # "the book on the table", "fewer apples than you"
            
            # Gerund as noun
            ['VBG'],                # "running" (as noun)
            ['DT', 'VBG'],          # "the running"
            
            # Past participle as adjective
            ['DT', 'VBN', 'NN'],    # "the hidden key"
            ['DT', 'VBN', 'NNS'],   # "the hidden keys"
            ['VBN', 'NN'],          # "hidden key"
            ['VBN', 'NNS'],         # "hidden keys"
            ['NN', 'NN'],           # "action movies"
            
            # Existential there
            ['EX'],                 # "there" (as in "there is")
            
            # ========================================
            # COORDINATION (NP CC NP)
            # ========================================
            ['NP', 'CC', 'NP'],     # "the cat and the dog"
            ['PRP', 'CC', 'PRP'],   # "he and i"
        ]
        
        # VP: Verb Phrase
        self.grammar['VP'] = [
            # Intransitive verbs
            ['VB'],                 # "run" (imperative)
            ['VBD'],                # "arrived"
            ['VBP'],                # "run" (non-3sg present)
            ['VBZ'],                # "runs" (3sg present)
            ['VBG'],                # "running"
            
            # Transitive verbs with NP object
            ['VB', 'NP'],           # "buy a book"
            ['VBD', 'NP'],          # "bought a book"
            ['VBP', 'NP'],          # "buy books"
            ['VBZ', 'NP'],          # "buys a book"
            ['VBG', 'NP'],          # "buying a book"
            ['VBN', 'NP'],          # "bought a book" (passive)
            
            # Ditransitive verbs (two objects)
            ['VB', 'NP', 'NP'],     # "give him a book"
            ['VBD', 'NP', 'NP'],    # "gave him a book"
            ['VBP', 'NP', 'NP'],    # "give him a book"
            ['VBZ', 'NP', 'NP'],    # "gives him a book"
            
            # Verb + PP
            ['VB', 'PP'],           # "go to the store"
            ['VBD', 'PP'],          # "went to the store"
            ['VBP', 'PP'],          # "go to the store"
            ['VBZ', 'PP'],          # "goes to the store"
            
            # Verb + NP + PP
            ['VB', 'NP', 'PP'],     # "buy a book for me"
            ['VBD', 'NP', 'PP'],    # "bought a book for me"
            ['VBP', 'NP', 'PP'],    # "buy a book for me"
            ['VBZ', 'NP', 'PP'],    # "buys a book for me"
            
            # Verb + adverb
            ['VB', 'RB'],           # "run quickly"
            ['VBD', 'RB'],          # "ran quickly"
            ['VBP', 'RB'],          # "run quickly"
            ['VBZ', 'RB'],          # "runs quickly"
            ['VB', 'RB', 'RB'],     # "run very quickly"
            ['VBD', 'RB', 'RB'],
            ['VBZ', 'RB', 'RB'],
            ['VB', 'RBR'],          # "run faster"
            ['VB', 'RBS'],
            
            # Verb + NP + adverb
            ['VBD', 'NP', 'RB'],    # "bought a book yesterday"
            ['VBP', 'NP', 'RB'],    # "buy a book today"
            ['VBZ', 'NP', 'RB'],    # "buys a book daily"
            
            # Modal + verb
            ['MD', 'VB'],           # "will go"
            ['MD', 'VB', 'NP'],     # "will buy a book"
            ['MD', 'VB', 'PP'],     # "will go to the store"
            ['MD', 'VB', 'NP', 'PP'],  # "will buy a book for me"
            
            # Modal perfect (could have done)
            ['MD', 'VB', 'VBN', 'NP'],   # "could have done it"
            ['MD', 'VB', 'VBN'],         # "could have gone"
            
            # Auxiliary constructions
            ['VBZ', 'VBG'],         # "is running"
            ['VBP', 'VBG'],
            ['VBD', 'VBG'],
            ['MD', 'VBG'],
            ['VBZ', 'VBG', 'NP'],   # "is buying a book"
            ['VBP', 'VBG', 'NP'],
            ['VBD', 'VBG', 'NP'],
            ['VBZ', 'VBN'],         # "was bought" (passive)
            ['VBP', 'VBN'],
            #['VBD', 'VBN'],
            ['VBZ', 'VBN', 'PP'],   # "was bought by me"
            ['VBP', 'VBN', 'PP'],
            ['VBD', 'VBN', 'PP'],
            
            # Negation
            ['VBZ', 'RB', 'VP'],    # "does n't like pizza"
            ['VBP', 'RB', 'VP'],    # "do n't want anything"
            ['MD', 'RB', 'VP'],     # "can't go"
            ['VBD', 'RB', 'VP'],    # "did n't go"
            
            # To-infinitive
            ['VB', 'TO', 'VB'],     # "want to go"
            ['VBD', 'TO', 'VB'],    # "wanted to go"
            ['VBP', 'TO', 'VB'],    # "want to go"
            ['VBZ', 'TO', 'VB'],    # "wants to go"
            ['VB', 'TO', 'VB', 'NP'],   # "want to buy a book"
            ['VBD', 'TO', 'VB', 'NP'],  # "wanted to buy a book"
            ['VBP', 'TO', 'VB', 'NP'],  # "want to buy a book"
            ['VBZ', 'TO', 'VB', 'NP'],  # "wants to buy a book"
            
            # Verb + adjective (linking verb)
            ['VBZ', 'JJ'],          # "is happy"
            ['VBZ', 'RB', 'JJ'],
            ['VBZ', 'JJR'],
            ['VBZ', 'JJS'],
            ['VBP', 'JJ'],          # "are happy"
            ['VBP', 'RB', 'JJ'],
            ['VBD', 'JJ'],          # "was happy"
            ['VBD', 'RB', 'JJ'],
            
            # Verb + particle (phrasal verbs)
            ['VB', 'RP'],           # "give up"
            ['VBD', 'RP'],          # "gave up"
            ['VBP', 'RP'],          # "give up"
            ['VBZ', 'RP'],          # "gives up"
            ['VB', 'RP', 'NP'],     # "pick up the book"
            ['VBD', 'RP', 'NP'],    # "picked up the book"
            
            
            # Copular verb + adverb phrase + PP (was quite far from)
            ['VBD', 'RB', 'PP'],    # "was quite far from the village"
            ['VBD', 'RB', 'RB', 'PP'],
            ['VBZ', 'RB', 'PP'],    # "is very close to the store"
            ['VBP', 'RB', 'PP'],    # "are quite far from here"
            
            # Copular verb + ADJP NP (is the most beautiful fruit)
            ['VBZ', 'JJ', 'NP'],    # "is the most beautiful fruit"
            ['VBZ', 'RB', 'JJ', 'NP'],
            ['VBZ', 'RBS', 'JJ', 'NP'],
            ['VBP', 'JJ', 'NP'],    # "are the best students"
            ['VBD', 'JJ', 'NP'],    # "was a happy child"
            
            # Verb + ADJP + NP (enjoy historical novels)
            ['VB', 'JJ', 'NP'],     # "enjoy historical novels"
            ['VB', 'RB', 'JJ', 'NP'],
            ['VBP', 'JJ', 'NP'],    # "enjoy historical novels"
            ['VBD', 'JJ', 'NP'],    # "enjoyed historical novels"
            ['VBZ', 'JJ', 'NP'],    # "enjoys historical novels"
            
            # Copular verb + ADJP + infinitive complement (was too cold to eat)
            ['VBD', 'JJ', 'PP'],    # "was too cold to eat"
            ['VBD', 'RB', 'JJ', 'PP'],
            ['VBZ', 'JJ', 'PP'],    # "is too cold to eat"
            ['VBP', 'JJ', 'PP'],    # "are too cold to eat"
            ['VBD', 'JJ', 'S'],     # "was too cold to eat" (with S complement)
            ['VBZ', 'JJ', 'S'],
            
            # ========================================
            # COORDINATION (VP CC VP)
            # ========================================
            ['VP', 'CC', 'VP'],     # "read and write", "runs and jumps"
        ]
        
        
        # PP: Prepositional Phrase
        self.grammar['PP'] = [
            ['IN', 'NP'],           # "in the house"
            ['TO', 'NP'],           # "to the store"
            ['IN', 'NP', 'PP'],     # "in the house on the hill"
            ['TO', 'VB'],           # "to eat" (infinitive complement)
        ]
    
    def get_grammar(self) -> Dict[str, List[List[str]]]:
        """Return the grammar rules."""
        return self.grammar
    
    def get_start_symbol(self) -> str:
        """Return the start symbol."""
        return self.start_symbol
    
    def deduplicate_rules(self):
        """Remove duplicate production rules from the grammar."""
        deduplicated = {}
        total_removed = 0
        
        for nt, prods in self.grammar.items():
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
        
        self.grammar = deduplicated
        if total_removed > 0:
            print(f"Removed {total_removed} duplicate rules")
        return total_removed
    
    def save_grammar(self, filepath: str):
        """Save grammar to a JSON file."""
        # Deduplicate before saving
        self.deduplicate_rules()
        
        data = {
            'start_symbol': self.start_symbol,
            'rules': self.grammar
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Grammar saved to {filepath}")
    
    @classmethod
    def load_grammar(cls, filepath: str) -> 'EnglishCFG':
        """Load grammar from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cfg = cls()
        cfg.grammar = data['rules']
        cfg.start_symbol = data['start_symbol']
        print(f"Grammar loaded from {filepath}")
        return cfg
    
    def save_cnf_grammar(self, filepath: str):
        """Convert grammar to CNF and save to a file."""
        from cnf_converter import CNFConverter
        
        # Convert to CNF
        converter = CNFConverter(self.grammar, self.start_symbol)
        cnf_grammar = converter.convert_to_cnf()
        
        # Deduplicate CNF rules
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
        
        if total_removed > 0:
            print(f"Removed {total_removed} duplicate CNF rules")
        
        # Save
        data = {
            'start_symbol': converter.start_symbol,
            'rules': deduplicated,
            'is_cnf': True
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"CNF Grammar saved to {filepath}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the grammar."""
        total_rules = sum(len(prods) for prods in self.grammar.values())
        non_terminals = list(self.grammar.keys())
        
        # Count terminals (POS tags that don't have productions)
        all_symbols = set()
        for prods in self.grammar.values():
            for prod in prods:
                all_symbols.update(prod)
        
        terminals = all_symbols - set(non_terminals)
        
        return {
            'start_symbol': self.start_symbol,
            'non_terminals': len(non_terminals),
            'terminals': len(terminals),
            'total_rules': total_rules,
            'non_terminal_list': non_terminals,
            'terminal_list': sorted(terminals)
        }
    
    def print_grammar(self):
        """Print the grammar in a readable format."""
        print("=" * 60)
        print("English CFG Grammar")
        print("=" * 60)
        print(f"Start symbol: {self.start_symbol}")
        print()
        
        for nt, prods in self.grammar.items():
            prod_strs = [' '.join(p) for p in prods]
            print(f"{nt} →")
            for ps in prod_strs:
                print(f"    | {ps}")
            print()


def main():
    """Demonstrate the English CFG."""
    
    # Create CFG
    cfg = EnglishCFG()
    
    # Print statistics
    stats = cfg.get_stats()
    print("=" * 60)
    print("English CFG - Penn Treebank Tags")
    print("=" * 60)
    print(f"Start symbol: {stats['start_symbol']}")
    print(f"Non-terminals: {stats['non_terminals']}")
    print(f"Terminals (POS tags): {stats['terminals']}")
    print(f"Total production rules: {stats['total_rules']}")
    print()
    
    print("Non-terminals:", stats['non_terminal_list'])
    print()
    print("Terminals (POS tags):", stats['terminal_list'])
    print()
    
    # Save grammar
    script_dir = Path(__file__).parent
    output_file = script_dir / "data" / "english_grammar.json"
    cfg.save_grammar(str(output_file))
    
    # Print some example rules
    print("=" * 60)
    print("Sample Rules:")
    print("=" * 60)
    
    for nt in ['S', 'NP', 'VP', 'PP']:
        prods = cfg.grammar[nt][:5]  # First 5 rules
        print(f"\n{nt} →")
        for p in prods:
            print(f"    | {' '.join(p)}")
        if len(cfg.grammar[nt]) > 5:
            print(f"    | ... ({len(cfg.grammar[nt]) - 5} more)")


if __name__ == "__main__":
    main()
