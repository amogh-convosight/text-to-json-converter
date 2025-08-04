#!/usr/bin/env python3
"""
Simple test to verify the converter works.
"""

import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from converter import UniversalTextToJSONConverter

# Create a simple schema
simple_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"}
    },
    "required": ["name", "age"]
}

# Simple test text
test_text = "John Doe is 25 years old and lives in San Francisco."

# Test the converter
try:
    converter = UniversalTextToJSONConverter()
    result = converter.convert(test_text, simple_schema)
    
    print("✅ Test passed!")
    print("Input:", test_text)
    print("Output:", json.dumps(result, indent=2))
    
except Exception as e:
    print("❌ Test failed!")
    print("Error:", str(e))
    sys.exit(1) 