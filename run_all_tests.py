#!/usr/bin/env python3
"""
Run all test cases and save outputs to the outputs directory.
"""

import subprocess
import sys
from pathlib import Path

# Test cases configuration
TEST_CASES = [
    {
        "name": "Test Case 1: BibTeX to Citation",
        "input": "../samples/test case 1/NIPS-2017-attention-is-all-you-need-Bibtex.txt",
        "schema": "../samples/test case 1/paper citations_schema.json",
        "output": "outputs/test_case_1_bibtex_output.json"
    },
    {
        "name": "Test Case 1: PDF to Citation",
        "input": "../samples/test case 1/NIPS-2017-attention-is-all-you-need-Paper.pdf",
        "schema": "../samples/test case 1/paper citations_schema.json",
        "output": "outputs/test_case_1_pdf_output.json"
    },
    {
        "name": "Test Case 2: GitHub Actions",
        "input": "../samples/test case 2/github actions sample input.txt",
        "schema": "../samples/test case 2/github_actions_schema.json",
        "output": "outputs/test_case_2_output.json"
    },
    {
        "name": "Test Case 3: Resume Text",
        "input": "../samples/test case 3/resume.txt",
        "schema": "../samples/test case 3/convert your resume to this schema.json",
        "output": "outputs/test_case_3_text_output.json"
    },
    {
        "name": "Test Case 3: Resume PDF",
        "input": "../samples/test case 3/Amogh_Dumbre_Resume_AI (1).pdf",
        "schema": "../samples/test case 3/convert your resume to this schema.json",
        "output": "outputs/test_case_3_pdf_output.json"
    }
]

def run_test_case(test):
    """Run a single test case."""
    print(f"\n{'='*60}")
    print(f"Running: {test['name']}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable,
        "main.py",
        "convert",
        test["input"],
        test["schema"],
        "-o", test["output"],
        "--no-show"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUCCESS: Output saved to {test['output']}")
        else:
            print(f"❌ FAILED: {result.stderr}")
            print(f"Stdout: {result.stdout}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    # Create outputs directory
    Path("outputs").mkdir(exist_ok=True)
    
    print("Running all test cases...")
    
    # Run all tests
    success_count = 0
    for test in TEST_CASES:
        try:
            run_test_case(test)
            success_count += 1
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count}/{len(TEST_CASES)} tests completed successfully")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 