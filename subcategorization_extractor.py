"""
Verb Subcategorization Extractor from VerbNet

This script extracts verb subcategorization frames from VerbNet
for each verb in our lexicon.

VerbNet provides:
- Syntactic frames: NP V NP, NP V PP, NP V NP PP, etc.
- Semantic roles: Agent, Theme, Recipient, etc.
- Example sentences

Output is used by the parser to validate verb-argument structures.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional

# NLTK VerbNet
import nltk
try:
    from nltk.corpus import verbnet
except LookupError:
    nltk.download('verbnet3', quiet=True)
    nltk.download('verbnet', quiet=True)
    from nltk.corpus import verbnet

# spaCy for lemmatization
import spacy
nlp = spacy.load('en_core_web_lg')


def get_lemma(word: str) -> str:
    """Get the lemma (base form) of a word using spaCy."""
    doc = nlp(word)
    if doc:
        return doc[0].lemma_.lower()
    return word.lower()


def analyze_frame_syntax(frame: Dict) -> Dict:
    """
    Analyze VerbNet frame syntax to determine what arguments are allowed.
    
    Returns a dict with:
    - allows_np: True if verb can take direct NP object
    - requires_pp: True if verb requires PP
    - pattern: simplified pattern string
    """
    syntax = frame.get('syntax', [])
    pos_sequence = [s.get('pos_tag', '') for s in syntax]
    
    description = frame.get('description', {})
    primary = description.get('primary', '')
    
    result = {
        'allows_np': False,
        'requires_pp': False,
        'allows_bare': False,  # Just the verb, no arguments
        'pattern': ' '.join(pos_sequence)
    }
    
    # Find verb position
    verb_idx = -1
    for i, pos in enumerate(pos_sequence):
        if pos == 'VERB':
            verb_idx = i
            break
    
    if verb_idx == -1:
        return result
    
    # What follows the verb?
    after_verb = pos_sequence[verb_idx + 1:]
    
    # Check patterns
    if not after_verb:
        result['allows_bare'] = True
        return result
    
    # NP immediately after verb = transitive
    if after_verb and after_verb[0] == 'NP':
        result['allows_np'] = True
    
    # PREP immediately after verb = PP required (intransitive with PP)
    if after_verb and after_verb[0] == 'PREP':
        result['requires_pp'] = True
        result['allows_bare'] = True  # Usually these verbs also allow bare form
    
    # ADJ after verb = copular
    if after_verb and after_verb[0] == 'ADJ':
        result['allows_np'] = True  # Copular verbs are flexible
    
    return result


def get_verbnet_frames(verb_lemma: str) -> Dict:
    """
    Get subcategorization info for a verb from VerbNet.
    
    Returns:
        Dict with 'frames' list and 'allows_np', 'requires_pp' flags
        
    Key logic:
    - allows_np: True if verb has any transitive frame (NP VERB NP)
    - requires_pp: True ONLY if verb has PP frames but NO transitive frames
    """
    result = {
        'frames': set(),
        'allows_np': False,
        'has_pp_frame': False,  # Track if any PP frame exists
        'allows_bare': False
    }
    
    try:
        classids = verbnet.classids(verb_lemma)
        
        for classid in classids:
            vn_frames = verbnet.frames(classid)
            
            for frame in vn_frames:
                analysis = analyze_frame_syntax(frame)
                
                if analysis['allows_np']:
                    result['allows_np'] = True
                    result['frames'].add('transitive')
                
                if analysis['requires_pp']:
                    result['has_pp_frame'] = True
                    result['frames'].add('intransitive')
                
                if analysis['allows_bare']:
                    result['allows_bare'] = True
                    result['frames'].add('intransitive')
        
        # Check for ditransitive (two NPs after verb)
        for classid in classids:
            class_name = classid.lower()
            if 'give' in class_name or 'send' in class_name:
                result['frames'].add('ditransitive')
    
    except Exception as e:
        pass
    
    # KEY: requires_pp only TRUE if verb has PP frames but NO transitive frames
    # e.g., "go" requires PP (no transitive), but "read" doesn't (has transitive)
    result['requires_pp'] = result['has_pp_frame'] and not result['allows_np']
    
    # Clean up temporary field
    del result['has_pp_frame']
    
    return result


def extract_subcategorization_from_lexicon(
    lexicon_path: str,
    output_path: str
) -> Dict:
    """
    Extract verb subcategorization for all verbs in the lexicon.
    
    Args:
        lexicon_path: Path to lexicon_with_features.json
        output_path: Path to save verb_subcategorization.json
        
    Returns:
        Dictionary of verb subcategorization frames
    """
    
    # Load lexicon
    with open(lexicon_path, 'r') as f:
        lexicon = json.load(f)
    
    print(f"Loaded lexicon with {len(lexicon)} words")
    
    # Find all verbs and get their lemmas
    verb_tags = {'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}
    verb_lemmas = set()
    
    for word, entries in lexicon.items():
        for entry in entries:
            if entry.get('pos') in verb_tags:
                lemma = entry.get('lemma', get_lemma(word))
                verb_lemmas.add(lemma)
    
    print(f"Found {len(verb_lemmas)} unique verb lemmas")
    
    # Extract subcategorization from VerbNet
    subcat = {
        "_description": "Verb subcategorization frames extracted from VerbNet",
        "_source": "NLTK VerbNet 3.0",
        "_frame_types": {
            "intransitive": "Verb takes no direct object (go, sleep)",
            "transitive": "Verb takes NP object (buy, read)",
            "ditransitive": "Verb takes two objects (give X Y)",
            "pp_required": "Verb requires PP complement (go to)",
            "pp_optional": "Verb can take optional PP",
            "np_pp": "Verb takes NP + PP (put X on Y)",
            "copular": "Linking verb (be, seem)"
        },
        "verbs": {}
    }
    
    found_count = 0
    not_found = []
    
    for lemma in sorted(verb_lemmas):
        vn_result = get_verbnet_frames(lemma)
        frames = vn_result['frames']
        
        if frames:
            # Store frames list plus important flags
            subcat['verbs'][lemma] = {
                'frames': sorted(list(frames)),
                'allows_np': vn_result['allows_np'],
                'requires_pp': vn_result['requires_pp']
            }
            found_count += 1
        else:
            not_found.append(lemma)
    
    print(f"Found VerbNet frames for {found_count} verbs")
    print(f"Not in VerbNet: {len(not_found)} verbs")
    
    # For verbs not in VerbNet, use a default (transitive is most common)
    for lemma in not_found:
        subcat['verbs'][lemma] = {
            'frames': ['transitive'],
            'allows_np': True,
            'requires_pp': False
        }
    
    # ========================================
    # MOTION VERB OVERRIDES
    # ========================================
    # Source: Beth Levin's "English Verb Classes and Alternations" (1993)
    # Motion verbs (run-51.3.2, escape-51.1, etc.) require directional PP
    # They don't allow bare NP objects in typical usage
    # 
    # "I went to the school" ✓ (with PP)
    # "I went the school" ✗ (bare NP - ungrammatical)
    # "go the distance" is an idiom, not productive usage
    
    MOTION_VERBS = {
        'go', 'come', 'travel', 'arrive', 
        'depart', 'return', 'proceed', 'advance', 'retreat',
        'enter', 'exit'
    }
    
    motion_override_count = 0
    for lemma in MOTION_VERBS:
        if lemma in subcat['verbs']:
            subcat['verbs'][lemma]['allows_np'] = False
            subcat['verbs'][lemma]['requires_pp'] = True
            motion_override_count += 1
    
    # Verbs requiring PP (not motion, but similar pattern)
    PP_VERBS = {'listen', 'smile', 'laugh', 'look', 'stare', 'glance'}
    
    for lemma in PP_VERBS:
        if lemma in subcat['verbs']:
            subcat['verbs'][lemma]['allows_np'] = False
            subcat['verbs'][lemma]['requires_pp'] = True
            motion_override_count += 1
    
    print(f"Applied motion verb overrides to {motion_override_count} verbs")
    
    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subcat, f, indent=2, sort_keys=True)
    
    print(f"\nSaved subcategorization for {len(subcat['verbs'])} verbs to {output_path}")
    
    return subcat


def show_examples(subcat: Dict):
    """Show example subcategorization frames."""
    
    print("\n" + "=" * 60)
    print("Sample Verb Subcategorization Frames")
    print("=" * 60)
    
    examples = ['go', 'buy', 'give', 'put', 'sleep', 'eat', 'be', 'seem', 'run', 'read']
    
    for verb in examples:
        if verb in subcat['verbs']:
            frames = subcat['verbs'][verb]
            print(f"  {verb:12} -> {frames}")


def main():
    """Main function."""
    
    script_dir = Path(__file__).parent
    lexicon_path = script_dir / "data" / "lexicon_with_features.json"
    output_path = script_dir / "data" / "verb_subcategorization.json"
    
    print("=" * 60)
    print("Extracting Verb Subcategorization from VerbNet")
    print("=" * 60 + "\n")
    
    # Check VerbNet is available
    print(f"VerbNet classes available: {len(verbnet.classids())}")
    
    subcat = extract_subcategorization_from_lexicon(
        str(lexicon_path),
        str(output_path)
    )
    
    show_examples(subcat)


if __name__ == "__main__":
    main()
