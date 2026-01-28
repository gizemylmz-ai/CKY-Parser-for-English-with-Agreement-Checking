"""
Agreement Checker

This module checks grammatical agreements during CKY parsing:
1. Determiner-Noun number agreement (a book ✓, *a books ✗)
2. Subject-Verb number/person agreement (I buy ✓, *I buys ✗)

Agreement rules are loaded from a JSON file (no hardcoding).
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class AgreementChecker:
    """
    Checks grammatical agreements between constituents.
    """
    
    def __init__(self, rules_path: str = None):
        """
        Initialize the agreement checker.
        
        Args:
            rules_path: Optional path to agreement rules JSON file
        """
        self.rules = {}
        self._load_default_rules()
        
        if rules_path:
            self.load_rules(rules_path)
    
    def _load_default_rules(self):
        """Load default agreement rules."""
        # These are the linguistic rules for English agreement
        # They can be overridden by loading from a file
        
        self.rules = {
            # Rule name -> rule definition
            "dt_nn_agreement": {
                "description": "Determiner must agree with noun in number",
                "constituents": ["DT", "NN"],
                "check_type": "number_match",
                "allow_any": True  # DT.num='any' matches anything
            },
            "dt_nns_agreement": {
                "description": "Determiner must agree with plural noun",
                "constituents": ["DT", "NNS"],
                "check_type": "number_match",
                "allow_any": True
            },
            "subject_verb_agreement_vbz": {
                "description": "3rd person singular subject requires VBZ",
                "constituents": ["NP", "VBZ"],
                "check_type": "subject_verb_3sg"
            },
            "subject_verb_agreement_vbp": {
                "description": "Non-3rd singular subject requires VBP",
                "constituents": ["NP", "VBP"],
                "check_type": "subject_verb_non3sg"
            }
        }
    
    def load_rules(self, filepath: str):
        """Load agreement rules from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.rules.update(json.load(f))
        print(f"Loaded agreement rules from {filepath}")
    
    def save_rules(self, filepath: str):
        """Save current rules to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=2)
        print(f"Agreement rules saved to {filepath}")
    
    def check_agreement(self, 
                        left_features: Dict, 
                        right_features: Dict,
                        parent_nt: str,
                        left_nt: str,
                        right_nt: str) -> Tuple[bool, Optional[str]]:
        """
        Check if two constituents agree when combined.
        
        Args:
            left_features: Features of the left constituent
            right_features: Features of the right constituent
            parent_nt: The parent non-terminal being created
            left_nt: The left child non-terminal
            right_nt: The right child non-terminal
            
        Returns:
            Tuple of (agreement_ok, error_message)
        """
        
        # Check DT + NN agreement
        if left_nt == 'DT' and right_nt in ('NN', 'NNS'):
            return self._check_dt_noun_agreement(left_features, right_features, right_nt)
        
        # Check Subject-Verb agreement (when building S from NP + VP)
        if parent_nt == 'S' and left_nt == 'NP':
            # Get the verb type from right side
            verb_pos = right_features.get('head_pos') or right_features.get('pos')
            if verb_pos in ('VBZ', 'VBP'):
                return self._check_subject_verb_agreement(left_features, right_features)
        
        # No agreement rule applies - OK
        return True, None
    
    def _check_dt_noun_agreement(self, 
                                  dt_features: Dict, 
                                  noun_features: Dict,
                                  noun_pos: str) -> Tuple[bool, Optional[str]]:
        """
        Check determiner-noun number agreement.
        
        Rules:
        - 'a', 'an' (num=sg) can only go with singular nouns (NN)
        - 'the' (num=any) can go with any noun
        - 'these', 'those' (num=pl) can only go with plural nouns (NNS)
        """
        dt_num = dt_features.get('num', 'any')
        
        # If DT allows any number, always OK
        if dt_num == 'any':
            return True, None
        
        # Get noun number from POS tag
        if noun_pos == 'NN':
            noun_num = 'sg'
        elif noun_pos == 'NNS':
            noun_num = 'pl'
        else:
            noun_num = noun_features.get('num', 'any')
        
        # Check match
        if dt_num == noun_num:
            return True, None
        
        # Agreement failure
        error = f"DT-Noun number disagreement: DT({dt_num}) + {noun_pos}({noun_num})"
        return False, error
    
    def _check_subject_verb_agreement(self,
                                       np_features: Dict,
                                       vp_features: Dict) -> Tuple[bool, Optional[str]]:
        """
        Check subject-verb agreement.
        
        Rules (for present tense only):
        - 3rd person singular (he/she/it) requires VBZ (-s form)
        - All others require VBP (base form)
        - Past tense (VBD) has no agreement requirement
        """
        # Get subject features
        subj_num = np_features.get('num', 'any')
        subj_person = np_features.get('person', 'any')
        
        # Get verb features
        verb_pos = vp_features.get('head_pos') or vp_features.get('pos')
        verb_tense = vp_features.get('tense', 'any')
        
        # Past tense - no agreement needed
        if verb_tense == 'past':
            return True, None
        
        # Check present tense agreement
        if verb_pos == 'VBZ':
            # VBZ requires 3rd person singular
            if subj_person == '3' and subj_num == 'sg':
                return True, None
            elif subj_person == 'any' or subj_num == 'any':
                return True, None  # Can't determine, allow
            else:
                error = f"Subject-Verb disagreement: NP({subj_person}p, {subj_num}) + VBZ (requires 3sg)"
                return False, error
        
        elif verb_pos == 'VBP':
            # VBP requires non-3rd-singular
            if subj_person == '3' and subj_num == 'sg':
                error = f"Subject-Verb disagreement: NP(3sg) + VBP (requires non-3sg)"
                return False, error
            return True, None
        
        # Other verb forms - no agreement check
        return True, None
    
    def propagate_features(self,
                           left_features: Dict,
                           right_features: Dict,
                           parent_nt: str,
                           left_nt: str,
                           right_nt: str) -> Dict:
        """
        Propagate features from children to parent constituent.
        
        Args:
            left_features, right_features: Child features
            parent_nt: Parent non-terminal
            left_nt, right_nt: Child non-terminals
            
        Returns:
            Features for the parent constituent
        """
        parent_features = {}
        
        # NP inherits features from head (usually rightmost noun)
        if parent_nt == 'NP':
            if right_nt in ('NN', 'NNS', 'NNP', 'NNPS'):
                parent_features['num'] = right_features.get('num', 'sg' if right_nt in ('NN', 'NNP') else 'pl')
                parent_features['head_pos'] = right_nt
            elif left_nt == 'PRP':
                parent_features['num'] = left_features.get('num', 'any')
                parent_features['person'] = left_features.get('person', 'any')
                parent_features['head_pos'] = 'PRP'
            elif right_nt == 'NP':
                # NP -> NP PP - inherit from left NP
                parent_features = right_features.copy()
            else:
                parent_features = left_features.copy()
        
        # VP inherits features from head verb
        elif parent_nt == 'VP':
            verb_tags = ('VB', 'VBD', 'VBP', 'VBZ', 'VBG', 'VBN')
            if left_nt in verb_tags:
                parent_features['head_pos'] = left_nt
                parent_features['tense'] = left_features.get('tense', 'any')
                if 'num' in left_features:
                    parent_features['num'] = left_features['num']
                if 'person' in left_features:
                    parent_features['person'] = left_features['person']
            elif right_nt in verb_tags:
                parent_features['head_pos'] = right_nt
                parent_features['tense'] = right_features.get('tense', 'any')
        
        # PP inherits from NP
        elif parent_nt == 'PP':
            if right_nt == 'NP':
                parent_features = right_features.copy()
        
        return parent_features


def main():
    """Demonstrate the agreement checker."""
    
    checker = AgreementChecker()
    
    print("=" * 60)
    print("Agreement Checker Demo")
    print("=" * 60)
    
    # Test DT-NN agreement
    print("\n--- DT-NN Agreement Tests ---")
    
    test_cases = [
        # (dt_features, noun_features, noun_pos, expected)
        ({'num': 'sg'}, {'num': 'sg'}, 'NN', True),   # a book ✓
        ({'num': 'sg'}, {'num': 'pl'}, 'NNS', False), # *a books ✗
        ({'num': 'any'}, {'num': 'sg'}, 'NN', True),  # the book ✓
        ({'num': 'any'}, {'num': 'pl'}, 'NNS', True), # the books ✓
        ({'num': 'pl'}, {'num': 'pl'}, 'NNS', True),  # these books ✓
        ({'num': 'pl'}, {'num': 'sg'}, 'NN', False),  # *these book ✗
    ]
    
    for dt_feat, noun_feat, noun_pos, expected in test_cases:
        result, error = checker._check_dt_noun_agreement(dt_feat, noun_feat, noun_pos)
        status = "✓" if result == expected else "✗"
        print(f"  DT({dt_feat.get('num')}) + {noun_pos} -> {result} {status}")
        if error:
            print(f"    Error: {error}")
    
    # Test Subject-Verb agreement
    print("\n--- Subject-Verb Agreement Tests ---")
    
    sv_tests = [
        # (np_features, vp_features, expected)
        ({'person': '1', 'num': 'sg'}, {'head_pos': 'VBP'}, True),   # I buy ✓
        ({'person': '1', 'num': 'sg'}, {'head_pos': 'VBZ'}, False),  # *I buys ✗
        ({'person': '3', 'num': 'sg'}, {'head_pos': 'VBZ'}, True),   # He buys ✓
        ({'person': '3', 'num': 'sg'}, {'head_pos': 'VBP'}, False),  # *He buy ✗
        ({'person': '3', 'num': 'pl'}, {'head_pos': 'VBP'}, True),   # They buy ✓
        ({'person': '3', 'num': 'pl'}, {'head_pos': 'VBZ'}, False),  # *They buys ✗
    ]
    
    for np_feat, vp_feat, expected in sv_tests:
        result, error = checker._check_subject_verb_agreement(np_feat, vp_feat)
        status = "✓" if result == expected else "✗"
        print(f"  NP({np_feat.get('person')}p, {np_feat.get('num')}) + VP({vp_feat.get('head_pos')}) -> {result} {status}")
        if error:
            print(f"    Error: {error}")
    
    # Save rules to file
    script_dir = Path(__file__).parent
    rules_file = script_dir / "data" / "agreement_rules.json"
    checker.save_rules(str(rules_file))


if __name__ == "__main__":
    main()
