#!/usr/bin/env python3
"""
Simple runner script for RelationOS analyzer
Runs the analyzer as a proper Python module
"""

import sys
from pathlib import Path

# Add the analyzer package to Python path
current_dir = Path(__file__).parent
analyzer_dir = current_dir / "analyzer"
sys.path.insert(0, str(analyzer_dir))

# Import and run the main function
from analyzer.main import main as analyzer_main

if __name__ == "__main__":
    sys.exit(analyzer_main())
