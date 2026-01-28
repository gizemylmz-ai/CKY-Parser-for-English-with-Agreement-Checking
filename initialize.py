#!/usr/bin/env python3
"""
Initializer Script for English Parser

Runs all prerequisite scripts to generate required data files
before the main parser can be used.

Usage:
    python initialize.py           # Generate all data files
    python initialize.py --run     # Generate files and run parser
"""

import subprocess
import sys
import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()


def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    script_path = SCRIPT_DIR / script_name
    
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Running: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SCRIPT_DIR),
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"✓ {script_name} completed successfully")
            return True
        else:
            print(f"✗ {script_name} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"✗ Error running {script_name}: {e}")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print("\n" + "="*60)
    print("Checking dependencies...")
    print("="*60)
    
    missing = []
    
    # Check spaCy
    try:
        import spacy
        print("✓ spaCy installed")
        # Check for model
        try:
            nlp = spacy.load('en_core_web_lg')
            print("✓ en_core_web_lg model loaded")
        except OSError:
            print("✗ en_core_web_lg model not found")
            print("  Run: python -m spacy download en_core_web_lg")
            missing.append("spacy model")
    except ImportError:
        print("✗ spaCy not installed")
        print("  Run: pip install spacy")
        missing.append("spacy")
    
    # Check NLTK
    try:
        import nltk
        print("✓ NLTK installed")
    except ImportError:
        print("✗ NLTK not installed")
        print("  Run: pip install nltk")
        missing.append("nltk")
    
    return len(missing) == 0


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           English Parser Initialization Script               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠ Please install missing dependencies and try again.")
        sys.exit(1)
    
    # Scripts to run in order
    scripts = [
        ("lexicon_generator.py", "Generate lexicon with morphological features"),
        ("english_cfg.py", "Generate CFG grammar rules"),
        ("subcategorization_extractor.py", "Extract verb subcategorization from VerbNet"),
    ]
    
    # Run each script
    success = True
    for script_name, description in scripts:
        if not run_script(script_name, description):
            success = False
            print(f"\n⚠ Initialization failed at: {script_name}")
            sys.exit(1)
    
    # Summary
    print("\n" + "="*60)
    print("Initialization Complete!")
    print("="*60)
    print("\nGenerated files:")
    print("  • data/lexicon_with_features.json")
    print("  • data/english_grammar.json")
    print("  • data/verb_subcategorization.json")
    
    # Check if --run flag was passed
    if len(sys.argv) > 1 and sys.argv[1] == '--run':
        print("\n" + "="*60)
        print("Starting English Parser...")
        print("="*60 + "\n")
        run_script("main.py", "Run English Parser")
    else:
        print("\nTo run the parser:")
        print("  python main.py")


if __name__ == "__main__":
    main()
