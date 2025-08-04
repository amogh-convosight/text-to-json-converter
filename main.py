#!/usr/bin/env python3
"""
Main entry point for the Universal Text-to-JSON Converter CLI.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli import app

if __name__ == "__main__":
    app() 