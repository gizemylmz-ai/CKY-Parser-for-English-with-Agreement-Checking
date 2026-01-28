"""
Morphological Preprocessor using spaCy

This module analyzes input sentences using spaCy to provide:
1. Word tokens
2. Disambiguated POS tags (one per word, based on context)
3. Morphological features (number, person, tense)

The disambiguator picks the correct POS tag based on context,
so we don't need to try all possible combinations.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Import spaCy for morphological analysis and disambiguation
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. Run: pip install spacy")


class MorphologicalPreprocessor:
    """
    Preprocesses sentences using spaCy for POS tagging and disambiguation.
    """
    
    def __init__(self, 
                 lexicon_path: str = None,
                 spacy_model: str = "en_core_web_lg"):
        """
        Initialize the preprocessor.
        
        Args:
            lexicon_path: Path to lexicon_with_features.json (for feature lookup)
            spacy_model: spaCy model to use for disambiguation
        """
        self.lexicon = {}
        self.nlp = None
        
        # Load lexicon for feature lookup
        if lexicon_path:
            self.load_lexicon(lexicon_path)
        
        # Load spaCy model for disambiguation
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(spacy_model)
                print(f"Loaded spaCy model: {spacy_model}")
            except OSError:
                print(f"spaCy model '{spacy_model}' not found.")
                print(f"Run: python -m spacy download {spacy_model}")
    
    def load_lexicon(self, filepath: str):
        """Load the lexicon from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.lexicon = json.load(f)
        print(f"Loaded lexicon with {len(self.lexicon)} words")
    
    def analyze_sentence(self, sentence: str) -> Dict[str, Any]:
        """
        Analyze a complete sentence using spaCy.
        
        spaCy performs disambiguation - it picks ONE POS tag per word
        based on the context of the sentence.
        
        Args:
            sentence: Input sentence string
            
        Returns:
            Dictionary with tokens, disambiguated POS tags, and features
        """
        if self.nlp is None:
            raise RuntimeError("spaCy model not loaded")
        
        # Use spaCy for tokenization and POS tagging
        doc = self.nlp(sentence)
        
        word_analyses = []
        pos_sequence = []
        
        for token in doc:
            # Skip punctuation
            if token.is_punct:
                continue
            
            word = token.text.lower()
            pos_tag = token.tag_  # Fine-grained Penn Treebank tag
            
            # Get morphological features from spaCy
            morph = token.morph.to_dict()
            
            # Build features dictionary
            features = {
                'word': word,
                'pos': pos_tag,
                'lemma': token.lemma_,
            }
            
            # Add number feature
            if 'Number' in morph:
                features['num'] = 'sg' if morph['Number'] == 'Sing' else 'pl'
            
            # Add person feature (for pronouns and verbs)
            if 'Person' in morph:
                features['person'] = morph['Person']
            
            # Add tense feature
            if 'Tense' in morph:
                features['tense'] = morph['Tense'].lower()
            
            # If we have a lexicon, try to get additional features
            if word in self.lexicon:
                for lex_entry in self.lexicon[word]:
                    if lex_entry.get('pos') == pos_tag:
                        # Merge lexicon features
                        for key, value in lex_entry.items():
                            if key not in features:
                                features[key] = value
                        break
            
            word_analyses.append({
                'word': word,
                'found': True,
                'analyses': [features]  # Single analysis (disambiguated)
            })
            pos_sequence.append(features)
        
        tokens = [wa['word'] for wa in word_analyses]
        
        return {
            'sentence': sentence,
            'tokens': tokens,
            'word_analyses': word_analyses,
            'all_words_found': True,
            'unknown_words': [],
            'pos_sequence': [entry['pos'] for entry in pos_sequence],
            'pos_sequences': [pos_sequence]  # Single sequence (disambiguated)
        }
    
    def format_analysis(self, result: Dict) -> str:
        """Format analysis result for display."""
        lines = []
        lines.append(f"Sentence: {result['sentence']}")
        lines.append(f"Tokens: {result['tokens']}")
        lines.append(f"POS Tags: {result['pos_sequence']}")
        lines.append("")
        
        lines.append("Word Analyses:")
        for wa in result['word_analyses']:
            for a in wa['analyses']:
                features = {k: v for k, v in a.items() if k not in ['word', 'pos', 'lemma']}
                lines.append(f"  {a['word']} ({a['pos']}): lemma={a['lemma']}, {features}")
        
        return '\n'.join(lines)


def main():
    """Demonstrate the morphological preprocessor."""
    
    # Load preprocessor
    script_dir = Path(__file__).parent
    lexicon_path = script_dir / "data" / "lexicon_with_features.json"
    
    preprocessor = MorphologicalPreprocessor(str(lexicon_path))
    
    # Test sentences - notice that spaCy disambiguates
    test_sentences = [
        "I bought a book",           # Grammatical
        "I buys a book",             # Ungrammatical - but spaCy will still tag it
        "She gives him two books",   # Grammatical
        "The big cat runs quickly",  # Grammatical
        "a books",                   # Ungrammatical
    ]
    
    print("=" * 60)
    print("Morphological Preprocessor Demo (with spaCy disambiguation)")
    print("=" * 60)
    
    for sentence in test_sentences:
        print("\n" + "-" * 40)
        result = preprocessor.analyze_sentence(sentence)
        print(preprocessor.format_analysis(result))


if __name__ == "__main__":
    main()
