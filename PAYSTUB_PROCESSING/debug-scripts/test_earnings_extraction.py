#!/usr/bin/env python3
"""
Test earnings data extraction with pdfplumber format
"""

import os
import pdfplumber
from regex_patterns.earnings_regex import extract_earnings_data

def test_earnings_extraction():
    """Test earnings data extraction on page 1."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("Testing earnings data extraction with pdfplumber format...")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        text = page1.extract_text()
        
        print(f"Text length: {len(text)}")
        print("Text relevant to earnings:")
        lines = text.split('\n')
        for i, line in enumerate(lines[10:20]):
            print(f"Line {i+11:2d}: {repr(line)}")
        print()
        
        # Test earnings extraction
        print("Testing earnings extraction:")
        earnings_data = extract_earnings_data(text, 1)
        print(f"Found {len(earnings_data)} earnings items:")
        for item in earnings_data:
            print(f"  {item}")

if __name__ == "__main__":
    test_earnings_extraction()