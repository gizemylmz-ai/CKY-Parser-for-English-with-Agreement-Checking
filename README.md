# CKY Parser for English with Agreement Checking

This project is a robust English parser that combines a **CKY (Cocke-Kasami-Younger) parser** with **morphological analysis** (via spaCy) and **grammatical agreement checking**. It parses English sentences using a custom Context-Free Grammar (CFG) defined with Penn Treebank POS tags.

## Key Features

1.  **Hybrid Approach**: Uses `spaCy` for accurate POS tagging and morphological feature extraction (disambiguation), and a CKY algorithm for syntactic parsing.
2.  **Context-Free Grammar**: A comprehensive English CFG supporting declarative sentences, imperatives, Yes/No questions, and Wh-questions.
3.  **Chomsky Normal Form (CNF)**: Automatically converts the CFG to CNF logic for the CKY algorithm.
4.  **Agreement Checking**: Validates grammatical agreements such as:
    *   Subject-Verb agreement (e.g., "He runs" vs *"He run")
    *   Determiner-Noun agreement (e.g., "These books" vs *"These book")
    *   Verb subcategorization (argument structure)
5.  **Parse Tree Construction**: Reconstructs the original CFG tree structure from the binary CNF tree for readable output.

## Installation & Requirements

The project utilizes Python and the `spaCy` library.

1.  **Install Dependencies**:
    ```bash
    pip install spacy
    ```

2.  **Download spaCy Model**:
    This project uses the large English model for better accuracy.
    ```bash
    python -m spacy download en_core_web_lg
    ```

## Usage

You can run the parser in three modes:

### 1. Interactive Mode
Run the script without arguments to enter an interactive shell where you can type sentences.
```bash
python main.py
```

### 2. Single Sentence
Pass a sentence as a command-line argument.
```bash
python main.py "The big cat runs quickly."
```

### 3. File Input
Parse a list of sentences from a text file (one sentence per line).
```bash
python main.py -f sentences.txt
```

## Evaluation

To evaluate the parser's performance against a gold standard dataset, run:
```bash
python parseval_evaluation_full.py
```
This script runs the parser on a set of test sentences, compares the resulting trees with gold standard trees, and reports **Precision**, **Recall**, and **F1-scores**.

## Project Structure

### Core Modules
*   **`main.py`**: The entry point. It orchestrates the entire pipeline: preprocessing -> parsing -> agreement checking -> tree conversion.
*   **`english_cfg.py`**: Defines the English Context-Free Grammar (CFG) using Penn Treebank tags.
*   **`cky_parser.py`**: Implements the CKY chart parsing algorithm. It handles the core parsing logic using CNF rules.
*   **`cnf_converter.py`**: Converts the structural CFG from `english_cfg.py` into Chomsky Normal Form (CNF) required by the CKY parser.
*   **`morphological_preprocessor.py`**: Uses `spaCy` to tokenize the input and provide disambiguated POS tags and morphological features (number, person, tense, lemma).
*   **`agreement_checker.py`**: Verifies grammatical correctness by checking agreement between constituents in the parse tree (e.g., matching plural subjects with plural verbs).
*   **`parse_tree_converter.py`**: Converts the binary trees produced by the CKY parser back into the original n-ary CFG format for display.

### Evaluation & Tools
*   **`parseval_evaluation_full.py`**: Runs evaluation metrics (Precision/Recall/F1) against a set of gold standard parse trees.
*   **`lexicon_generator.py`**: Generates a rich lexicon JSON file by extracting features from words using spaCy.
*   **`subcategorization_extractor.py`**: Helps in extracting or managing verb subcategorization frames (rules about what arguments a verb requires, e.g., transitive vs. intransitive).
*   **`data/`**: Directory containing JSON files for grammar rules, lexicon data, and agreement rules.

## How It Works

1.  **Input**: The user provides a sentence.
2.  **Preprocessing**: `morphological_preprocessor.py` (using spaCy) analyzes the sentence to determine the correct POS tag for each word (disambiguation) and extracts features (like "plural", "3rd person").
3.  **Grammar Loading**: `main.py` loads the CFG from `english_cfg.py` and uses `cnf_converter.py` to create a CNF version for the parser.
4.  **Parsing**: `cky_parser.py` attempts to parse the sequence of POS tags. It builds a chart of possible trees.
5.  **Agreement Check**: During or after parsing, `agreement_checker.py` verifies that the combined nodes satisfy grammatical rules.
6.  **Reconstruction**: `parse_tree_converter.py` takes the valid CNF tree and converts it back to the original CFG structure.
7.  **Output**: The application prints the grammatical status, the parse tree (if valid), and any errors found.

## Example Output

```text
Sentence: The big cat runs quickly.
✓ GRAMMATICAL
POS Sequence: DT JJ NN VBZ RB

Parse Tree:
(S
  (NP
    (DT the)
    (JJ big)
    (NN cat))
  (VP
    (VBZ runs)
    (RB quickly)))

Bracket: (S (NP (DT the) (JJ big) (NN cat)) (VP (VBZ runs) (RB quickly)))
```


## Contributors

- @gizemylmz-ai
- @atahanuz
