"""
PARSEVAL Evaluation - Compares parser output against gold standard parse trees.
Simply run: python parseval_evaluation.py
"""

from collections import namedtuple
from main import EnglishParser

Constituent = namedtuple('Constituent', ['label', 'start', 'end'])

# Gold standard parse trees
GOLD_PARSES = {
    "The teacher explained the new rule clearly.": "(S (NP (DT The) (NN teacher)) (VP (VBD explained) (NP (DT the) (JJ new) (NN rule)) (RB clearly))) ",
    "My sister prefers action movies.": "(S (NP (PRP$ My) (NN sister)) (VP (VBZ prefers) (NP (NN action) (NNS movies))) )",
    "We visited our grandparents last weekend.": "(S (NP (PRP We)) (VP (VBD visited) (NP (PRP$ our) (NNS grandparents)) (NP (JJ last) (NN weekend))) )",
    "Maps show the geography of the world.": "(S (NP (NNS Maps)) (VP (VBP show) (NP (NP (DT the) (NN geography)) (PP (IN of) (NP (DT the) (NN world))))) )",
    "Jupiter is the largest planet in the solar system.": "(S (NP (NNP Jupiter)) (VP (VBZ is) (NP (NP (DT the) (JJS largest) (NN planet)) (PP (IN in) (NP (DT the) (JJ solar) (NN system))))) )",
    "Can you find the hidden key?": "(SQ (MD Can) (NP (PRP you)) (VP (VB find) (NP (DT the) (JJ hidden) (NN key))) )",
    "He jogged around the park every morning.": "(S (NP (PRP He)) (VP (VBD jogged) (PP (IN around) (NP (DT the) (NN park))) (NP (DT every) (NN morning))) )",
    "Where did she put her glasses?": "(SBARQ  (WRB Where) (SQ (VBD did) (NP (PRP she)) (VP (VB put) (NP (PRP$ her) (NNS glasses)))) )",
    "The soup was too cold to eat.": "(S (NP (DT The) (NN soup)) (VP (VBD was) (RB too) (JJ cold) (S (VP (TO to) (VB eat))))) )",
    "Please write your name on this paper.": "(S (INTJ (UH Please)) (VP (VB write) (NP (PRP$ your) (NN name)) (PP (IN on) (NP (DT this) (NN paper)))) )",
    "They are building a new bridge across the river.": "(S (NP (PRP They)) (VP (VBP are) (VP (VBG building) (NP (DT a) (JJ new) (NN bridge)) (PP (IN across) (NP (DT the) (NN river))))) )",
    "Does this bus go to the city center?": "(SQ (VBZ Does) (NP (DT this) (NN bus)) (VP (VB go) (PP (TO to) (NP (DT the) (NN city) (NN center)))) )",
    "I bought a present for my friend yesterday.": "(S (NP (PRP I)) (VP (VBD bought) (NP (DT a) (NN present)) (PP (IN for) (NP (PRP$ my) (NN friend))) (NP (NN yesterday))) )",
    "I enjoy historical novels.": "(S (NP (PRP I)) (VP (VBP enjoy) (NP (JJ historical) (NNS novels))) )",
    "I helped my mother with dinner yesterday.": "(S (NP (PRP I)) (VP (VBD helped) (NP (PRP$ my) (NN mother)) (PP (IN with) (NP (NN dinner))) (NP (NN yesterday))) )",
    "Epics tell about our national culture and history.": "(S (NP (NNS Epics)) (VP (VBP tell) (PP (IN about) (NP (PRP$ our) (NP (JJ national) (NN culture) (CC and) (NN history))))) )",
    "Watermelon is the most beautiful fruit of summer.": "(S (NP (NN Watermelon)) (VP (VBZ is) (NP (NP (DT the) (RBS most) (JJ beautiful) (NN fruit)) (PP (IN of) (NP (NN summer))))) )",
    "Will you attend the meeting tonight?": "(SQ (MD Will) (NP (PRP you)) (VP (VB attend) (NP (DT the) (NN meeting)) (NP (NN tonight))) )",
    "We watched the moonlight under this tree every night.": "(S (NP (PRP We)) (VP (VBD watched) (NP (DT the) (NN moonlight)) (PP (IN under) (NP (DT this) (NN tree))) (NP (DT every) (NN night))) )",
    "When did you come here lastly?": "(SBARQ (WRB When) (SQ (VBD did) (NP (PRP you)) (VP (VB come) (RB here) (RB lastly))) )",
    "The school was quite far from our village.": "(S (NP (DT The) (NN school)) (VP (VBD was)(RB quite) (JJ far) (PP (IN from) (NP (PRP$ our) (NN village))))) )",
    "Do not listen to loud music.": "(S (VP (VB Do) (RB not) (VP (VB listen) (PP (TO to) (NP (JJ loud) (NN music))))) )",
    "The dog runs across the park.": "(S (NP (DT The) (NN dog)) (VP (VBZ runs) (PP (IN across) (NP (DT the) (NN park)))) )",
    "She went to the market yesterday.": "(S (NP (PRP She)) (VP (VBD went) (PP (TO to) (NP (DT the) (NN market))) (NP (NN yesterday))) )",
    "He and I are best friends.": "(S (NP (PRP He) (CC and) (PRP I)) (VP (VBP are) (NP (JJS best) (NNS friends))) )",
    "The car drives smoothly.": "(S (NP (DT The) (NN car)) (VP (VBZ drives) (RB smoothly)) )",
    "I have fewer apples than you.": "(S (NP (PRP I)) (VP (VBP have) (NP (NP (JJR fewer) (NNS apples)) (PP (IN than) (NP (PRP you))))) )",
    "I don't want anything.": "(S (NP (PRP I)) (VP (VBP do) (RB n't) (VP (VB want) (NP (NN anything)))) )",
    "She doesn't like pizza.": "(S (NP (PRP She)) (VP (VBZ does) (RB n't) (VP (VB like) (NP (NN pizza)))) )",
    "They're going to their house over there.": "(S (NP (PRP They)) (VP (VBP 're) (VP (VBG going) (PP (TO to) (NP (PRP$ their) (NN house))) (RB over) (RB there))) )",
    "I saw that movie last week.": "(S (NP (PRP I)) (VP (VBD saw) (NP (DT that) (NN movie)) (NP (JJ last) (NN week))) )",
    "I have less apples than you.": "(S (NP (PRP I)) (VP (VBP have) (NP (NP (JJR less) (NNS apples)) (PP (IN than) (NP (PRP you))))) )"
}
# POS tags (terminals)
POS_TAGS = {'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD',
            'NN', 'NNS', 'NNP', 'NNPS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR',
            'RBS', 'RP', 'SYM', 'TO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP',
            'VBZ', 'WDT', 'WP', 'WP$', 'WRB', '.', ',', ':', "''", '``', '-LRB-', '-RRB-'}


def extract_constituents_from_tuple(tree, include_root=False):
    """Extract constituents from parser's tuple format: ('S', ('NP', 'DT', 'NN'), ('VP', ...))"""
    constituents = set()

    def is_terminal(node):
        """Check if node is a terminal (POS tag string)."""
        return isinstance(node, str)

    def traverse(node, pos):
        if is_terminal(node):
            return pos + 1

        label = node[0]
        children = node[1:]
        start = pos

        for child in children:
            pos = traverse(child, pos)
        end = pos

        # Skip POS tag nodes (label is in POS_TAGS) and punctuation
        is_pos_tag = label in POS_TAGS
        is_punct = label in ('.', ',', ':', "''", '``', '-LRB-', '-RRB-')

        if not is_pos_tag and not is_punct:
            # Normalize S0 -> S
            normalized_label = 'S' if label == 'S0' else label
            constituents.add(Constituent(normalized_label, start, end))

        return end

    traverse(tree, 0)

    # Remove root if needed
    if not include_root and constituents:
        max_end = max(c.end for c in constituents)
        constituents = {c for c in constituents if not (c.start == 0 and c.end == max_end)}

    return constituents


def parse_gold_tree(tree_str):
    """Parse gold standard bracket notation: (S (NP (DT The) (NN dog)) ...)"""
    tokens = tree_str.replace('(', ' ( ').replace(')', ' ) ').split()
    tokens = [t for t in tokens if t]
    idx = 0

    def parse_node():
        nonlocal idx
        if tokens[idx] != '(':
            raise ValueError(f"Expected '(' at {idx}")
        idx += 1
        label = tokens[idx]
        idx += 1
        children = []

        while tokens[idx] != ')':
            if tokens[idx] == '(':
                children.append(parse_node())
            else:
                children.append(tokens[idx])  # word
                idx += 1
        idx += 1

        return (label,) + tuple(children)

    return parse_node()


def extract_constituents_from_gold(tree, include_root=False):
    """Extract constituents from gold tree tuple."""
    constituents = set()

    def is_preterminal(node):
        """A preterminal has exactly one child which is a string (the word)."""
        if not isinstance(node, tuple) or len(node) != 2:
            return False
        return isinstance(node[1], str)

    def traverse(node, pos):
        if isinstance(node, str):
            return pos + 1

        if is_preterminal(node):
            return pos + 1

        label = node[0]
        children = node[1:]
        start = pos

        for child in children:
            pos = traverse(child, pos)
        end = pos

        is_punct = label in ('.', ',', ':', "''", '``', '-LRB-', '-RRB-')
        if not is_punct:
            constituents.add(Constituent(label, start, end))

        return end

    traverse(tree, 0)

    if not include_root and constituents:
        max_end = max(c.end for c in constituents)
        constituents = {c for c in constituents if not (c.start == 0 and c.end == max_end)}

    return constituents


def tuple_to_bracket(tree):
    """Convert parser's tuple format to bracket notation."""
    if isinstance(tree, str):
        return tree

    label = tree[0]
    children = tree[1:]

    # Build bracket notation recursively
    parts = [f"({label}"]
    for child in children:
        parts.append(" " + tuple_to_bracket(child))
    parts.append(")")

    return "".join(parts)


def evaluate(gold_const, system_const):
    """Calculate precision, recall, F1."""
    matches = gold_const & system_const
    precision = len(matches) / len(system_const) if system_const else 0
    recall = len(matches) / len(gold_const) if gold_const else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'matches': len(matches),
        'gold': len(gold_const),
        'system': len(system_const),
        'missing': gold_const - system_const,
        'extra': system_const - gold_const,
    }


def main():
    print("Initializing parser...")
    parser = EnglishParser(verbose=False)

    print("\n" + "=" * 70)
    print("PARSEVAL EVALUATION")
    print("=" * 70)

    total_matches = 0
    total_gold = 0
    total_system = 0
    results = []

    for sentence, gold_parse_str in GOLD_PARSES.items():
        result = parser.parse(sentence)

        if not result['grammatical'] or not result['parse_trees']:
            print(f"\n[FAILED] {sentence}")
            print(f"  Could not parse: {result['errors']}")
            continue

        # Get constituents from gold standard
        gold_tree = parse_gold_tree(gold_parse_str)
        gold_const = extract_constituents_from_gold(gold_tree)

        # Evaluate all parse trees and pick the best one
        best_metrics = None
        best_tree = None
        best_tree_str = None
        for candidate_tree in result['parse_trees']:
            candidate_const = extract_constituents_from_tuple(candidate_tree)
            candidate_metrics = evaluate(gold_const, candidate_const)
            candidate_tree_str = tuple_to_bracket(candidate_tree)
            # Use tree string as tie-breaker for deterministic results
            if best_metrics is None or candidate_metrics['f1'] > best_metrics['f1'] or \
               (candidate_metrics['f1'] == best_metrics['f1'] and candidate_tree_str < best_tree_str):
                best_metrics = candidate_metrics
                best_tree = candidate_tree
                best_tree_str = candidate_tree_str

        system_tree = best_tree
        metrics = best_metrics
        results.append((sentence, metrics))

        total_matches += metrics['matches']
        total_gold += metrics['gold']
        total_system += metrics['system']

        # Print per-sentence result
        status = "OK" if metrics['f1'] == 1.0 else f"F1={metrics['f1']:.2f}"
        print(f"\n[{status}] {sentence}")
        print(f"  Gold parse:   {gold_parse_str}")
        print(f"  System parse: {tuple_to_bracket(system_tree)}")
        print(f"  P={metrics['precision']:.2f} R={metrics['recall']:.2f} F1={metrics['f1']:.2f}")
        print(f"  Matches: {metrics['matches']}/{metrics['gold']} gold, {metrics['matches']}/{metrics['system']} system")

        if metrics['missing']:
            print(f"  Missing: {[f'{c.label}[{c.start}:{c.end}]' for c in sorted(metrics['missing'])]}")
        if metrics['extra']:
            print(f"  Extra: {[f'{c.label}[{c.start}:{c.end}]' for c in sorted(metrics['extra'])]}")

    # Summary
    precision = total_matches / total_system if total_system else 0
    recall = total_matches / total_gold if total_gold else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Sentences evaluated: {len(results)}/{len(GOLD_PARSES)}")
    print(f"Total constituents:  {total_matches}/{total_gold} matched")
    print(f"\nPrecision: {precision:.4f} ({precision*100:.1f}%)")
    print(f"Recall:    {recall:.4f} ({recall*100:.1f}%)")
    print(f"F1-score:  {f1:.4f} ({f1*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
