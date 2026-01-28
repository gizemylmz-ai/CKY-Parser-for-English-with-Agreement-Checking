"""
English Parser - Main Orchestrator

This is the main entry point that integrates all modules:
1. Morphological Preprocessor - tokenizes and analyzes words
2. CFG Grammar - English grammar with Penn Treebank tags
3. CNF Converter - converts CFG to Chomsky Normal Form
4. CKY Parser - parses sentences using the CNF grammar
5. Agreement Checker - validates grammatical agreements
6. Parse Tree Converter - converts CNF trees to original CFG format

Usage:
    python main.py                    # Interactive mode
    python main.py "sentence"         # Parse a single sentence
    python main.py -f sentences.txt   # Parse sentences from file
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import all modules
from morphological_preprocessor import MorphologicalPreprocessor
from english_cfg import EnglishCFG
from cnf_converter import CFGtoCNFConverter
from cky_parser import CKYParser
from parse_tree_converter import ParseTreeConverter
from agreement_checker import AgreementChecker


class EnglishParser:
    """
    Complete English parser with agreement checking.
    """
    
    def __init__(self, 
                 lexicon_path: str = None,
                 grammar_path: str = None,
                 subcat_path: str = None,
                 verbose: bool = False):
        """
        Initialize the parser.
        
        Args:
            lexicon_path: Path to lexicon_with_features.json
            grammar_path: Path to english_grammar.json (optional)
            subcat_path: Path to verb_subcategorization.json (optional)
            verbose: Print detailed output
        """
        self.verbose = verbose
        
        # Get default paths
        script_dir = Path(__file__).parent
        if lexicon_path is None:
            lexicon_path = script_dir / "data" / "lexicon_with_features.json"
        if grammar_path is None:
            grammar_path = script_dir / "data" / "english_grammar.json"
        if subcat_path is None:
            subcat_path = script_dir / "data" / "verb_subcategorization.json"
        
        # Initialize components
        print("Initializing English Parser...")
        
        # 1. Load morphological preprocessor
        self.preprocessor = MorphologicalPreprocessor(str(lexicon_path))
        
        # 2. Load grammar (initially structural)
        if Path(grammar_path).exists():
            self.cfg = EnglishCFG.load_grammar(str(grammar_path))
        else:
            print("Creating new CFG grammar...")
            self.cfg = EnglishCFG()
            self.cfg.save_grammar(str(grammar_path))
            
        # 3. Initialize CNF converter and CKY parser with structural grammar
        # This keeps POS tags as terminals for the CKY chart-filling logic.
        self.cnf_converter = CFGtoCNFConverter()
        print("Converting structural grammar to CNF...")
        self.cnf_converter.parse_grammar(self.cfg.get_grammar(), self.cfg.get_start_symbol())
        self.cnf_converter.convert_to_cnf()
        
        self.cky_parser = CKYParser()
        self.cky_parser.load_grammar_from_converter(self.cnf_converter)
        
        # 4. Add lexicon terminals to the CFG grammar (for JSON and tree display)
        # We do this AFTER CKY initialization to keep the CNF structural-only.
        self.lexicon_pos_tags = set()
        self._load_lexicon_terminals()
        
        # 5. Initialize tree converter with the full grammar (now includes terminals)
        self.tree_converter = ParseTreeConverter()
        self.tree_converter.load_original_grammar(self.cfg.get_grammar())
        
        # 6. Initialize agreement checker
        self.agreement_checker = AgreementChecker()
        
        # 7. Load verb subcategorization frames
        self.verb_subcat = {}
        if Path(subcat_path).exists():
            with open(subcat_path, 'r') as f:
                data = json.load(f)
                self.verb_subcat = data.get('verbs', {})
            print(f"Loaded {len(self.verb_subcat)} verb subcategorization frames")
        
        print("Parser initialized successfully!\n")

    def _load_lexicon_terminals(self):
        """
        Load terminals from lexicon JSON files and add them to the CFG grammar.
        """
        script_dir = Path(__file__).parent
        lexicon_dir = script_dir / "data"
        
        files = [
            lexicon_dir / "closed_class_pos_tags.json",
            lexicon_dir / "open_class_pos_tags.json"
        ]
        
        total_terminals = 0
        for file_path in files:
            if not file_path.exists():
                print(f"Warning: Lexicon file {file_path} not found.")
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lexicon_data = json.load(f)
                
            for pos, words in lexicon_data.items():
                self.lexicon_pos_tags.add(pos)
                if pos not in self.cfg.grammar:
                    self.cfg.grammar[pos] = []
                
                # Add each word as a terminal production [word]
                for word in words:
                    production = [word.lower()]
                    if production not in self.cfg.grammar[pos]:
                        self.cfg.grammar[pos].append(production)
                        total_terminals += 1
                        
        print(f"Added {total_terminals} terminal rules from lexicon to grammar.")
    
    def parse(self, sentence: str) -> Dict[str, Any]:
        """
        Parse a sentence.
        
        Args:
            sentence: Input sentence string
            
        Returns:
            Dictionary with parsing results
        """
        result = {
            'sentence': sentence,
            'grammatical': False,
            'parse_trees': [],
            'pos_sequence': [],
            'errors': [],
            'word_analyses': []
        }
        
        # Step 1: Morphological analysis (spaCy disambiguates - one POS per word)
        morph_result = self.preprocessor.analyze_sentence(sentence)
        result['word_analyses'] = morph_result['word_analyses']
        result['tokens'] = morph_result['tokens']
        
        # Get the single disambiguated POS sequence
        pos_sequence = morph_result['pos_sequences'][0]  # Only one from spaCy
        pos_tags = [entry['pos'] for entry in pos_sequence]
        features = pos_sequence
        
        result['pos_sequence'] = pos_tags
        
        if self.verbose:
            print(f"POS tags: {' '.join(pos_tags)}")
        
        # Step 2: Check agreements BEFORE parsing
        feature_dict = {i: feat for i, feat in enumerate(features)}
        agreement_ok, agree_errors = self._check_tree_agreements(
            None, feature_dict, pos_tags
        )
        
        if not agreement_ok:
            result['errors'].extend(agree_errors)
            result['grammatical'] = False
            if self.verbose:
                for err in agree_errors:
                    print(f"  Agreement error: {err}")
            return result
        
        # Step 3: CKY parse with the actual tokens (words) but constrained by spaCy tags.
        # This gives us the best of both worlds: robust disambiguation from spaCy
        # and the full parse tree with words as leaves from our grammar.
        tokens_lower = [t.lower() for t in result['tokens']]
        success, trees = self.cky_parser.parse(tokens_lower, pos_constraints=pos_tags, verbose=False)
        
        if success and trees:
            # Success! Convert all trees to original CFG format
            result['grammatical'] = True
            for tree in trees:
                original_tree = self.tree_converter.convert(tree)
                result['parse_trees'].append(original_tree)
            
            if self.verbose:
                print(f"  Parse successful!")
        else:
            result['errors'].append("No valid parse found for POS sequence")
            result['grammatical'] = False
        
        return result
    
    def _check_tree_agreements(self, 
                                tree: Tuple,
                                features: Dict[int, Dict],
                                pos_tags: List[str]) -> Tuple[bool, List[str]]:
        """
        Check agreements in a parse tree.
        
        This is a simplified version - for a complete implementation,
        we would need to track features through the tree structure.
        
        Args:
            tree: Parse tree (tuple format)
            features: Dictionary mapping position to features
            pos_tags: List of POS tags
            
        Returns:
            Tuple of (all_agreements_ok, list_of_errors)
        """
        errors = []
        
        # Check DT-NN agreement (including DT + JJ* + NN/NNS patterns)
        # Find DT and look for the noun it modifies (may have adjectives in between)
        i = 0
        while i < len(pos_tags):
            if pos_tags[i] == 'DT':
                dt_idx = i
                dt_features = features[i]
                
                # Find the noun after the determiner (skip adjectives)
                j = i + 1
                while j < len(pos_tags) and pos_tags[j] in ('JJ', 'JJR', 'JJS', 'RB'):
                    j += 1
                
                # Check if we found a noun
                if j < len(pos_tags) and pos_tags[j] in ('NN', 'NNS'):
                    noun_features = features[j]
                    ok, error = self.agreement_checker._check_dt_noun_agreement(
                        dt_features, noun_features, pos_tags[j]
                    )
                    if not ok:
                        errors.append(error)
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
        
        # Check subject-verb agreement
        # Find subject: various patterns at start of sentence
        subj_features = None
        subj_description = ""
        
        # ========================================
        # SUBJECT DETECTION PATTERNS
        # ========================================
        
        # 1. PRP subject (I, he, she, they, etc.)
        if pos_tags[0] == 'PRP':
            subj_features = features[0]
            subj_description = f"PRP({subj_features.get('person', '?')}p, {subj_features.get('num', '?')})"
        
        # 2. DT + NN/NNS subject (the cat, the cats)
        elif len(pos_tags) >= 2 and pos_tags[0] == 'DT' and pos_tags[1] in ('NN', 'NNS'):
            noun_num = 'sg' if pos_tags[1] == 'NN' else 'pl'
            subj_features = {'num': noun_num, 'person': '3'}
            subj_description = f"NP(3p, {noun_num})"
        
        # 3. DT + JJ + NN/NNS subject (the big cat)
        elif len(pos_tags) >= 3 and pos_tags[0] == 'DT' and pos_tags[1] == 'JJ' and pos_tags[2] in ('NN', 'NNS'):
            noun_num = 'sg' if pos_tags[2] == 'NN' else 'pl'
            subj_features = {'num': noun_num, 'person': '3'}
            subj_description = f"NP(3p, {noun_num})"
        
        # 4. Bare NNP/NNPS subject (John, Americans)
        elif pos_tags[0] in ('NNP', 'NNPS'):
            noun_num = 'sg' if pos_tags[0] == 'NNP' else 'pl'
            subj_features = {'num': noun_num, 'person': '3'}
            subj_description = f"NP(3p, {noun_num})"
        
        # 5. Bare NNS subject - PLURAL (Cats run)
        elif pos_tags[0] == 'NNS':
            subj_features = {'num': 'pl', 'person': '3'}
            subj_description = "NP(3p, pl)"
        
        # 6. Bare NN subject - SINGULAR (Coffee is good)
        elif pos_tags[0] == 'NN':
            subj_features = {'num': 'sg', 'person': '3'}
            subj_description = "NP(3p, sg)"
        
        # 7. PRP$ + NN/NNS subject (My cat runs, My cats run)
        elif len(pos_tags) >= 2 and pos_tags[0] == 'PRP$' and pos_tags[1] in ('NN', 'NNS'):
            noun_num = 'sg' if pos_tags[1] == 'NN' else 'pl'
            subj_features = {'num': noun_num, 'person': '3'}
            subj_description = f"NP(3p, {noun_num})"
        
        # 8. PRP$ + JJ + NN/NNS subject (My big cat runs)
        elif len(pos_tags) >= 3 and pos_tags[0] == 'PRP$' and pos_tags[1] == 'JJ' and pos_tags[2] in ('NN', 'NNS'):
            noun_num = 'sg' if pos_tags[2] == 'NN' else 'pl'
            subj_features = {'num': noun_num, 'person': '3'}
            subj_description = f"NP(3p, {noun_num})"
        
        # 9. There-insertion (There is/are books)
        # "There" is EX, verb agrees with post-verbal NP
        elif pos_tags[0] == 'EX':
            # Find the NP after the verb
            for i, pos in enumerate(pos_tags[1:], 1):
                if pos in ('NN', 'NNS', 'NNP', 'NNPS'):
                    noun_num = 'sg' if pos in ('NN', 'NNP') else 'pl'
                    subj_features = {'num': noun_num, 'person': '3'}
                    subj_description = f"EX+NP(3p, {noun_num})"
                    break
                elif pos in ('PRP',):
                    subj_features = features[i]
                    subj_description = f"EX+PRP({subj_features.get('person', '?')}p, {subj_features.get('num', '?')})"
                    break
        
        # 10. Coordinated subject (The cat and the dog run) - ALWAYS PLURAL
        # Check for CC (and, or) in subject position
        if subj_features is None or 'CC' in pos_tags[:5]:
            # Look for NP CC NP pattern at start
            cc_idx = None
            for i in range(min(5, len(pos_tags))):
                if pos_tags[i] == 'CC':
                    cc_idx = i
                    break
            
            if cc_idx is not None and cc_idx > 0:
                # Check if there's a noun before and after CC
                has_noun_before = any(p in ('NN', 'NNS', 'NNP', 'NNPS', 'PRP') for p in pos_tags[:cc_idx])
                has_noun_after = cc_idx + 1 < len(pos_tags) and any(
                    p in ('NN', 'NNS', 'NNP', 'NNPS', 'PRP', 'DT') for p in pos_tags[cc_idx+1:cc_idx+3]
                )
                if has_noun_before and has_noun_after:
                    # Coordinated subjects are ALWAYS plural
                    subj_features = {'num': 'pl', 'person': '3'}
                    subj_description = "NP+CC+NP(3p, pl)"
        
        # 11. Indefinite pronouns (everyone, everybody, someone, nobody, etc.)
        # These are tagged as NN but are singular
        SINGULAR_INDEFINITES = {'everyone', 'everybody', 'someone', 'somebody', 
                                 'anyone', 'anybody', 'no one', 'nobody',
                                 'everything', 'something', 'anything', 'nothing'}
        PLURAL_INDEFINITES = {'many', 'few', 'several', 'both'}
        
        if subj_features is None and len(pos_tags) > 0:
            first_word = features[0].get('lemma', '').lower() if features else ''
            if first_word in SINGULAR_INDEFINITES:
                subj_features = {'num': 'sg', 'person': '3'}
                subj_description = f"INDEF({first_word}, 3p, sg)"
            elif first_word in PLURAL_INDEFINITES:
                subj_features = {'num': 'pl', 'person': '3'}
                subj_description = f"INDEF({first_word}, 3p, pl)"
        
        # 12. Quantifiers: "All of the water is...", "Some of the books are..."
        # Pattern: DT + IN + DT + NN/NNS - number comes from inner NP
        if subj_features is None and len(pos_tags) >= 4:
            if pos_tags[0] == 'DT' and pos_tags[1] == 'IN' and pos_tags[2] == 'DT':
                for i in range(3, min(6, len(pos_tags))):
                    if pos_tags[i] in ('NN', 'NNS'):
                        noun_num = 'sg' if pos_tags[i] == 'NN' else 'pl'
                        subj_features = {'num': noun_num, 'person': '3'}
                        subj_description = f"QUANT(3p, {noun_num})"
                        break
        
        # Find main verb
        verb_idx = None
        verb_pos = None
        for i, pos in enumerate(pos_tags):
            if pos in ('VBZ', 'VBP'):
                verb_idx = i
                verb_pos = pos
                break
        
        if subj_features is not None and verb_idx is not None:
            verb_features = features[verb_idx]
            verb_features_with_head = {'head_pos': verb_pos, **verb_features}
            
            ok, error = self.agreement_checker._check_subject_verb_agreement(
                subj_features, verb_features_with_head
            )
            if not ok:
                errors.append(error)
        
        # Check verb subcategorization
        subcat_errors = self._check_verb_subcategorization(pos_tags, features)
        errors.extend(subcat_errors)
        
        return len(errors) == 0, errors
    
    def _check_verb_subcategorization(self, 
                                       pos_tags: List[str],
                                       features: Dict[int, Dict]) -> List[str]:
        """
        Check verb subcategorization (argument structure).
        
        Catches errors like:
        - "I went the school" (intransitive verb with direct object)
        - "I put the book" (missing required PP)
        
        Args:
            pos_tags: List of POS tags
            features: Dictionary mapping position to features
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Find main verb and analyze its arguments
        verb_idx = None
        verb_lemma = None
        verb_pos = None
        
        verb_tags = ('VB', 'VBD', 'VBP', 'VBZ', 'VBG', 'VBN')
        
        for i, pos in enumerate(pos_tags):
            if pos in verb_tags:
                verb_idx = i
                verb_pos = pos
                # Get lemma from features
                verb_lemma = features[i].get('lemma', '').lower()
                break
        
        if verb_lemma is None or verb_lemma not in self.verb_subcat:
            return errors  # Unknown verb, skip check
        
        verb_info = self.verb_subcat[verb_lemma]
        
        # Handle both old list format and new dict format
        if isinstance(verb_info, dict):
            allows_np = verb_info.get('allows_np', True)
            requires_pp = verb_info.get('requires_pp', False)
            frames = verb_info.get('frames', [])
        else:
            # Old format: list of frame types
            frames = verb_info
            allows_np = 'transitive' in frames or 'ditransitive' in frames
            requires_pp = 'pp_required' in frames
        
        # Analyze what follows the verb
        after_verb = pos_tags[verb_idx + 1:] if verb_idx < len(pos_tags) - 1 else []
        
        # Determine argument structure
        has_np = False
        has_pp = False
        
        # Check for NP immediately after verb (DT + NN, PRP, NNP, etc.)
        if after_verb:
            if after_verb[0] in ('DT', 'PRP', 'NNP', 'NNPS', 'CD', 'PRP$'):
                has_np = True
            elif after_verb[0] in ('NN', 'NNS'):
                has_np = True
        
        # Check for PP (IN + NP)
        for i, pos in enumerate(after_verb):
            if pos == 'IN' and i + 1 < len(after_verb):
                has_pp = True
                break
        
        # Validate based on allows_np and requires_pp flags
        # 
        # Rules:
        # 1. If verb requires_pp and has NP without PP -> error (e.g., "put the book")
        # 2. If verb allows_np=False and has NP without PP -> error (e.g., "went the school")
        # 3. If verb requires_pp and has NP with PP -> OK (e.g., "put the book on table")
        
        if has_np and not has_pp:
            # NP without PP
            if requires_pp:
                errors.append(f"Verb '{verb_lemma}' requires a preposition with its object")
            elif not allows_np:
                errors.append(f"Verb '{verb_lemma}' does not take a direct object (NP)")
        
        if requires_pp and not has_pp and not has_np and verb_idx < len(pos_tags) - 1:
            # Has something after verb but no PP at all
            errors.append(f"Verb '{verb_lemma}' requires a prepositional phrase")
        
        return errors
    
    def format_result(self, result: Dict) -> str:
        """Format parsing result for display."""
        lines = []
        lines.append(f"Sentence: {result['sentence']}")
        lines.append(f"Tokens: {result.get('tokens', [])}")
        lines.append("")
        
        if result['grammatical']:
            lines.append("✓ GRAMMATICAL")
            lines.append(f"POS Sequence: {' '.join(result['pos_sequence'])}")
            lines.append("")
            lines.append("Parse Tree:")
            if result['parse_trees']:
                tree_str = self.tree_converter.format_tree(result['parse_trees'][0])
                lines.append(tree_str)
                lines.append("")
                lines.append(f"Bracket: {self.tree_converter.format_tree_bracket(result['parse_trees'][0])}")
        else:
            lines.append("✗ UNGRAMMATICAL")
            if result['errors']:
                lines.append("Errors:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    lines.append(f"  - {error}")
        
        return '\n'.join(lines)


def main():
    """Main entry point."""
    
    # Initialize parser
    parser = EnglishParser(verbose=True)
    
    valid_sentences = [
        "I bought a present for my friend yesterday.",
        "I enjoy historical novels.",
        "I helped my mother with dinner yesterday.",
        "Epics tell about our national culture and history.",
        "Watermelon is the most beautiful fruit of summer.",
        "Will you attend the meeting tonight?",
        "We watched the moonlight under this tree every night.",
        "When did you come here lastly?",
        "The school was quite far from our village.",
        "Do not listen to loud music."
    ]
    invalid_sentences = [
        "I buys a gift for my friend.",
        "I read a historical novels.",
        "I will help my father yesterday.",
        "I went the school.",
        "I was read the book.", 
        "I went in the school.",
    ]

    # Test sentences
    test_sentences = [
        # Grammatical sentences
        "I bought a book",
        "The big cat runs quickly",
        "She gives him two books",
        "Will you attend the meeting",
        
        # Ungrammatical sentences (should fail)
        "I buys a book",           # Subject-verb disagreement
        "I bought a books",        # DT-NN disagreement
        "These book is good"       # DT-NN disagreement
    ]
    
    print("=" * 70)
    print("English Parser - Test Results")
    print("=" * 70)
    
    for sentence in valid_sentences:
        print("\n" + "-" * 60)
        result = parser.parse(sentence)
        print(parser.format_result(result))

    for sentence in invalid_sentences:
        print("\n" + "-" * 60)
        result = parser.parse(sentence)
        print(parser.format_result(result))
    
    # Interactive mode if no arguments
    if len(sys.argv) == 1:
        print("\n" + "=" * 70)
        print("Interactive Mode (type 'quit' to exit)")
        print("=" * 70)
        
        while True:
            try:
                sentence = input("\nEnter sentence: ").strip()
                if sentence.lower() in ('quit', 'exit', 'q'):
                    break
                if sentence:
                    result = parser.parse(sentence)
                    print()
                    print(parser.format_result(result))
            except EOFError:
                break
    
    # Command line arguments
    elif len(sys.argv) >= 2:
        if sys.argv[1] == '-f' and len(sys.argv) >= 3:
            # Parse sentences from file
            with open(sys.argv[2], 'r') as f:
                for line in f:
                    sentence = line.strip()
                    if sentence:
                        print("\n" + "-" * 60)
                        result = parser.parse(sentence)
                        print(parser.format_result(result))
        else:
            # Parse single sentence from command line
            sentence = ' '.join(sys.argv[1:])
            result = parser.parse(sentence)
            print(parser.format_result(result))


if __name__ == "__main__":
    main()
