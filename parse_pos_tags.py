"""
Penn Treebank POS Tag Parser

This script reads the Penn Treebank corpus, separates words by their POS tags
into closed-class and open-class categories, and saves them as dictionaries.

Output format: {pos_tag: [word1, word2, ...]}
"""

import nltk
from collections import defaultdict
import json

# Download required NLTK data (run once)
try:
    nltk.data.find('corpora/treebank')
except LookupError:
    nltk.download('treebank')


# Define closed-class (function words) and open-class (content words) POS tags
# Based on Penn Treebank tagset

CLOSED_CLASS_TAGS = {
    # Determiners
    'DT',    # Determiner (the, a, an)
    'PDT',   # Predeterminer (all, both)
    'WDT',   # Wh-determiner (which, that)
    
    # Pronouns
    'PRP',   # Personal pronoun (I, you, he)
    'PRP$',  # Possessive pronoun (my, your, his)
    'WP',    # Wh-pronoun (who, what)
    'WP$',   # Possessive wh-pronoun (whose)
    
    # Prepositions and Conjunctions
    'IN',    # Preposition or subordinating conjunction
    'CC',    # Coordinating conjunction (and, or, but)
    
    # Particles and Modals
    'RP',    # Particle (up, off)
    'MD',    # Modal (can, will, should)
    'TO',    # "to" as preposition or infinitive marker
    
    # Existential and Possessive
    'EX',    # Existential there
    'POS',   # Possessive ending ('s)
    
    # Interjections and other
    'UH',    # Interjection (uh, oh)
}

OPEN_CLASS_TAGS = {
    # Nouns
    'NN',    # Noun, singular or mass
    'NNS',   # Noun, plural
    'NNP',   # Proper noun, singular
    'NNPS',  # Proper noun, plural
    
    # Verbs
    'VB',    # Verb, base form
    'VBD',   # Verb, past tense
    'VBG',   # Verb, gerund or present participle
    'VBN',   # Verb, past participle
    'VBP',   # Verb, non-3rd person singular present
    'VBZ',   # Verb, 3rd person singular present
    
    # Adjectives
    'JJ',    # Adjective
    'JJR',   # Adjective, comparative
    'JJS',   # Adjective, superlative
    
    # Adverbs
    'RB',    # Adverb
    'RBR',   # Adverb, comparative
    'RBS',   # Adverb, superlative
    'WRB',   # Wh-adverb (where, when)
    
    # Numbers and Foreign Words
    'CD',    # Cardinal number
    'FW',    # Foreign word
    
    # Symbols (can be considered open class as they are content-bearing)
    'SYM',   # Symbol
    'LS',    # List item marker
}


def parse_penn_treebank():
    """
    Parse the Penn Treebank corpus and categorize words by POS tags.
    All words are stored in lowercase and are unique per tag.
    
    Returns:
        tuple: (closed_class_dict, open_class_dict, uncategorized_dict)
    """
    from nltk.corpus import treebank
    
    # Initialize dictionaries with sets for automatic uniqueness
    closed_class = defaultdict(set)
    open_class = defaultdict(set)
    uncategorized = defaultdict(set)
    
    # Get all tagged words from the treebank
    tagged_words = treebank.tagged_words()
    
    print(f"Total tagged words in Penn Treebank: {len(tagged_words)}")
    
    # Process each word-tag pair
    for word, tag in tagged_words:
        # Convert word to lowercase for consistency
        word_lower = word.lower()
        
        if tag in CLOSED_CLASS_TAGS:
            closed_class[tag].add(word_lower)
        elif tag in OPEN_CLASS_TAGS:
            open_class[tag].add(word_lower)
        else:
            # Punctuation and other tags go here
            uncategorized[tag].add(word_lower)
    
    # Convert sets to sorted lists for JSON serialization
    closed_class_dict = {tag: sorted(list(words)) for tag, words in closed_class.items()}
    open_class_dict = {tag: sorted(list(words)) for tag, words in open_class.items()}
    uncategorized_dict = {tag: sorted(list(words)) for tag, words in uncategorized.items()}
    
    return closed_class_dict, open_class_dict, uncategorized_dict


def save_to_json(data, filename):
    """Save dictionary to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {filename}")


def print_summary(closed_class, open_class, uncategorized):
    """Print a summary of the parsed data."""
    print("\n" + "="*60)
    print("PARSING SUMMARY")
    print("="*60)
    
    print("\n--- CLOSED CLASS POS TAGS ---")
    print(f"Number of tag types: {len(closed_class)}")
    total_closed = sum(len(words) for words in closed_class.values())
    print(f"Total unique words: {total_closed}")
    for tag, words in sorted(closed_class.items()):
        print(f"  {tag}: {len(words)} words")
    
    print("\n--- OPEN CLASS POS TAGS ---")
    print(f"Number of tag types: {len(open_class)}")
    total_open = sum(len(words) for words in open_class.values())
    print(f"Total unique words: {total_open}")
    for tag, words in sorted(open_class.items()):
        print(f"  {tag}: {len(words)} words")
    
    print("\n--- UNCATEGORIZED (Punctuation, etc.) ---")
    print(f"Number of tag types: {len(uncategorized)}")
    for tag, words in sorted(uncategorized.items()):
        print(f"  {tag}: {len(words)} tokens")
    
    print("\n" + "="*60)


def main():
    """Main function to parse and save POS tag data."""
    print("Parsing Penn Treebank corpus...")
    
    # Parse the corpus
    closed_class, open_class, uncategorized = parse_penn_treebank()
    
    # Print summary
    print_summary(closed_class, open_class, uncategorized)
    
    # Save to JSON files
    save_to_json(closed_class, 'data/closed_class_pos_tags.json')
    save_to_json(open_class, 'data/open_class_pos_tags.json')
    
    # Optionally save uncategorized (punctuation, etc.)
    save_to_json(uncategorized, 'data/uncategorized_pos_tags.json')
    
    print("\n✓ All files saved successfully!")
    
    # Display sample output
    print("\n--- SAMPLE OUTPUT ---")
    print("\nClosed Class (first 3 tags):")
    for i, (tag, words) in enumerate(list(closed_class.items())[:3]):
        print(f"  '{tag}': {words[:5]}{'...' if len(words) > 5 else ''}")
    
    print("\nOpen Class (first 3 tags):")
    for i, (tag, words) in enumerate(list(open_class.items())[:3]):
        print(f"  '{tag}': {words[:5]}{'...' if len(words) > 5 else ''}")


if __name__ == "__main__":
    main()
