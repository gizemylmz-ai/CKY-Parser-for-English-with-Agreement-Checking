"""
Lexicon Generator with Morphological Features

This module creates a lexicon file by:
1. Loading Penn Treebank POS tagged words from existing JSON files
2. Using spaCy to extract morphological features (number, person, tense)
3. Saving the enriched lexicon to a JSON file

The output lexicon is used by the CKY parser for agreement checking.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Try to import spaCy, provide instructions if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. Run: pip install spacy")
    print("Then download model: python -m spacy download en_core_web_lg")


class LexiconGenerator:
    """
    Generates a lexicon with morphological features from Penn Treebank data.
    """
    
    def __init__(self, spacy_model: str = "en_core_web_lg"):
        """
        Initialize the lexicon generator.
        
        Args:
            spacy_model: Name of the spaCy model to use for morphological analysis
        """
        self.lexicon = {}
        self.nlp = None
        self.spacy_model = spacy_model
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(spacy_model)
                print(f"Loaded spaCy model: {spacy_model}")
            except OSError:
                print(f"spaCy model '{spacy_model}' not found.")
                print(f"Run: python -m spacy download {spacy_model}")
    
    def load_pos_data(self, filepath: str) -> Dict[str, List[str]]:
        """
        Load POS tagged words from a JSON file.
        
        Args:
            filepath: Path to the JSON file (format: {POS_TAG: [words]})
            
        Returns:
            Dictionary mapping POS tags to word lists
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {sum(len(v) for v in data.values())} words from {filepath}")
        return data
    
    def get_morphological_features(self, word: str, pos_tag: str) -> Dict[str, Any]:
        """
        Extract morphological features using spaCy.
        
        Args:
            word: The word to analyze
            pos_tag: The Penn Treebank POS tag
            
        Returns:
            Dictionary of morphological features
        """
        features = {
            'word': word,
            'pos': pos_tag,
            'lemma': word,  # Default to same word
        }
        
        if self.nlp is None:
            # If spaCy not available, infer features from POS tag
            features.update(self._infer_features_from_pos(word, pos_tag))
            return features
        
        # Use spaCy for morphological analysis
        doc = self.nlp(word)
        if len(doc) > 0:
            token = doc[0]
            features['lemma'] = token.lemma_
            
            # Extract morph features
            morph = token.morph.to_dict()
            
            # Map spaCy morph features to our format
            if 'Number' in morph:
                features['num'] = 'sg' if morph['Number'] == 'Sing' else 'pl'
            
            if 'Person' in morph:
                features['person'] = morph['Person']
            
            if 'Tense' in morph:
                features['tense'] = morph['Tense'].lower()
            
            if 'VerbForm' in morph:
                features['verb_form'] = morph['VerbForm'].lower()
        
        # Also use POS tag to infer features (as backup/supplement)
        inferred = self._infer_features_from_pos(word, pos_tag)
        for key, value in inferred.items():
            if key not in features:
                features[key] = value
        
        return features
    
    def _infer_features_from_pos(self, word: str, pos_tag: str) -> Dict[str, Any]:
        """
        Infer morphological features from Penn Treebank POS tag.
        
        POS tag meanings:
        - NN: Noun, singular
        - NNS: Noun, plural
        - NNP: Proper noun, singular
        - NNPS: Proper noun, plural
        - VB: Verb, base form
        - VBD: Verb, past tense
        - VBG: Verb, gerund/present participle
        - VBN: Verb, past participle
        - VBP: Verb, non-3rd person singular present
        - VBZ: Verb, 3rd person singular present
        - PRP: Personal pronoun
        - DT: Determiner
        - CD: Cardinal number
        - etc.
        """
        features = {}
        
        # Noun number
        if pos_tag in ('NN', 'NNP'):
            features['num'] = 'sg'
        elif pos_tag in ('NNS', 'NNPS'):
            features['num'] = 'pl'
        
        # Verb tense and agreement
        if pos_tag == 'VB':
            features['tense'] = 'base'
            features['verb_form'] = 'inf'
        elif pos_tag == 'VBD':
            features['tense'] = 'past'
        elif pos_tag == 'VBG':
            features['tense'] = 'pres'
            features['verb_form'] = 'ger'
        elif pos_tag == 'VBN':
            features['tense'] = 'past'
            features['verb_form'] = 'part'
        elif pos_tag == 'VBP':
            features['tense'] = 'pres'
            features['num'] = 'non3sg'  # Not 3rd person singular
        elif pos_tag == 'VBZ':
            features['tense'] = 'pres'
            features['num'] = 'sg'
            features['person'] = '3'
        
        # Pronouns - infer person and number from common pronouns
        if pos_tag == 'PRP':
            pronoun_features = {
                'i': {'num': 'sg', 'person': '1'},
                'me': {'num': 'sg', 'person': '1'},
                'we': {'num': 'pl', 'person': '1'},
                'us': {'num': 'pl', 'person': '1'},
                'you': {'num': 'any', 'person': '2'},
                'he': {'num': 'sg', 'person': '3'},
                'him': {'num': 'sg', 'person': '3'},
                'she': {'num': 'sg', 'person': '3'},
                'her': {'num': 'sg', 'person': '3'},
                'it': {'num': 'sg', 'person': '3'},
                'they': {'num': 'pl', 'person': '3'},
                'them': {'num': 'pl', 'person': '3'},
            }
            if word.lower() in pronoun_features:
                features.update(pronoun_features[word.lower()])
        
        # Determiners - infer number compatibility
        if pos_tag == 'DT':
            det_number = {
                'a': 'sg',
                'an': 'sg',
                'the': 'any',
                'this': 'sg',
                'that': 'sg',
                'these': 'pl',
                'those': 'pl',
                'some': 'any',
                'all': 'any',
                'any': 'any',
                'no': 'any',
                'every': 'sg',
                'each': 'sg',
                'either': 'sg',
                'neither': 'sg',
                'both': 'pl',
            }
            if word.lower() in det_number:
                features['num'] = det_number[word.lower()]
        
        # Cardinal numbers (CD)
        if pos_tag == 'CD':
            word_lower = word.lower().strip()
            
            # Singular numbers: one, 1, 1.0, zero, 0
            singular_patterns = ['one', 'zero', '0', '1']
            
            # Check for exact singular match
            if word_lower in singular_patterns:
                features['num'] = 'sg'
            # Check for numeric "1" at the start (like "1.0", "1.00")
            elif word_lower.startswith('1.') or word_lower.startswith('1,'):
                # Numbers like 1.5 are typically plural ("1.5 books")
                # But 1.0 could be singular
                try:
                    num_val = float(word_lower.replace(',', ''))
                    features['num'] = 'sg' if num_val == 1.0 else 'pl'
                except ValueError:
                    features['num'] = 'pl'
            else:
                # All other numbers are plural
                features['num'] = 'pl'
        
        return features
    
    def build_lexicon(self, 
                      closed_class_file: str, 
                      open_class_file: str,
                      output_file: str = None) -> Dict[str, Dict]:
        """
        Build the complete lexicon from POS data files.
        
        Args:
            closed_class_file: Path to closed class POS tags JSON
            open_class_file: Path to open class POS tags JSON
            output_file: Optional path to save the lexicon
            
        Returns:
            The complete lexicon dictionary
        """
        # Load both POS data files
        closed_class = self.load_pos_data(closed_class_file)
        open_class = self.load_pos_data(open_class_file)
        
        # Merge all POS data
        all_pos_data = {**closed_class, **open_class}
        
        # Build lexicon with features
        self.lexicon = {}
        total_words = sum(len(words) for words in all_pos_data.values())
        processed = 0
        
        print(f"Processing {total_words} words...")
        
        for pos_tag, words in all_pos_data.items():
            for word in words:
                features = self.get_morphological_features(word, pos_tag)
                
                # A word might have multiple POS tags, store as list
                if word not in self.lexicon:
                    self.lexicon[word] = []
                
                # Check if this POS already exists for word
                existing_pos = [entry['pos'] for entry in self.lexicon[word]]
                if pos_tag not in existing_pos:
                    self.lexicon[word].append(features)
                
                processed += 1
                if processed % 1000 == 0:
                    print(f"  Processed {processed}/{total_words} words...")
        
        print(f"Lexicon built with {len(self.lexicon)} unique words")
        
        # Save to file if specified
        if output_file:
            self.save_lexicon(output_file)
        
        return self.lexicon
    
    def save_lexicon(self, filepath: str):
        """Save the lexicon to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.lexicon, f, indent=2, ensure_ascii=False)
        print(f"Lexicon saved to {filepath}")
    
    def load_lexicon(self, filepath: str) -> Dict[str, List[Dict]]:
        """Load a lexicon from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.lexicon = json.load(f)
        print(f"Loaded lexicon with {len(self.lexicon)} words from {filepath}")
        return self.lexicon
    
    def lookup(self, word: str) -> List[Dict]:
        """
        Look up a word in the lexicon.
        
        Args:
            word: The word to look up
            
        Returns:
            List of possible analyses (word might have multiple POS tags)
        """
        # Try exact match first
        if word in self.lexicon:
            return self.lexicon[word]
        
        # Try lowercase
        if word.lower() in self.lexicon:
            return self.lexicon[word.lower()]
        
        # Word not found
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the lexicon."""
        if not self.lexicon:
            return {'error': 'Lexicon is empty'}
        
        pos_counts = defaultdict(int)
        words_with_features = defaultdict(int)
        
        for word, entries in self.lexicon.items():
            for entry in entries:
                pos_counts[entry['pos']] += 1
                if 'num' in entry:
                    words_with_features['num'] += 1
                if 'person' in entry:
                    words_with_features['person'] += 1
                if 'tense' in entry:
                    words_with_features['tense'] += 1
        
        return {
            'total_words': len(self.lexicon),
            'total_entries': sum(len(v) for v in self.lexicon.values()),
            'pos_counts': dict(pos_counts),
            'feature_counts': dict(words_with_features)
        }


def main():
    """Build the lexicon from Penn Treebank data."""
    
    # Paths (relative to script location)
    script_dir = Path(__file__).parent
    closed_class_file = script_dir / "data" / "closed_class_pos_tags.json"
    open_class_file = script_dir / "data" / "open_class_pos_tags.json"
    output_file = script_dir / "data" / "lexicon_with_features.json"
    
    # Create generator and build lexicon
    generator = LexiconGenerator()
    
    lexicon = generator.build_lexicon(
        closed_class_file=str(closed_class_file),
        open_class_file=str(open_class_file),
        output_file=str(output_file)
    )
    
    # Print statistics
    stats = generator.get_stats()
    print("\n" + "=" * 50)
    print("Lexicon Statistics:")
    print("=" * 50)
    print(f"  Total unique words: {stats['total_words']}")
    print(f"  Total entries (word-POS pairs): {stats['total_entries']}")
    print(f"  Words with 'num' feature: {stats['feature_counts'].get('num', 0)}")
    print(f"  Words with 'person' feature: {stats['feature_counts'].get('person', 0)}")
    print(f"  Words with 'tense' feature: {stats['feature_counts'].get('tense', 0)}")
    
    print("\nPOS tag distribution:")
    for pos, count in sorted(stats['pos_counts'].items(), key=lambda x: -x[1])[:10]:
        print(f"  {pos}: {count}")
    
    # Example lookups
    print("\n" + "=" * 50)
    print("Example Lookups:")
    print("=" * 50)
    
    test_words = ['books', 'buys', 'the', 'i', 'went', 'two', 'gave']
    for word in test_words:
        entries = generator.lookup(word)
        if entries:
            print(f"\n  {word}:")
            for entry in entries:
                print(f"    {entry}")
        else:
            print(f"\n  {word}: NOT FOUND")


if __name__ == "__main__":
    main()
