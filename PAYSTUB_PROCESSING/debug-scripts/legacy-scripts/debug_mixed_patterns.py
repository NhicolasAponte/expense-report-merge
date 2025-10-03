#!/usr/bin/env python3
"""
Debug script to test mixed bullet/asterisk pattern detection across all sections.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from regex_patterns.earnings_regex import extract_earnings_data_pdfplumber
from regex_patterns.deductions_regex import extract_tax_deductions_data_pdfplumber, extract_deductions_data_pdfplumber
from common_utils import get_pdf_path
import pdfplumber

def test_mixed_patterns():
    """Test that all sections can handle mixed bullet/asterisk patterns"""
    
    # Get the PDF file
    pdf_path = get_pdf_path()
    print(f"Testing mixed pattern detection with: {pdf_path}")
    
    # Test with page 1 (which we know has mixed patterns)
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < 1:
            print("ERROR: PDF has no pages")
            return
            
        page = pdf.pages[0]  # Page 1 (0-indexed)
        text = page.extract_text()
        
        if not text:
            print("ERROR: No text found on page 1")
            return
        
        print(f"\n=== PAGE 1 ANALYSIS ===")
        
        # Show raw text around section headers
        lines = text.split('\n')
        print(f"Total lines: {len(lines)}")
        
        print(f"\n--- Section Headers Found ---")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(keyword in line_stripped.upper() for keyword in ['EARNINGS', 'TAX DEDUCTIONS', 'DEDUCTIONS', 'DIRECT']):
                print(f"Line {i+1}: '{line_stripped}'")
        
        # Test earnings extraction
        print(f"\n--- EARNINGS EXTRACTION ---")
        earnings_data = extract_earnings_data_pdfplumber(text, page_num=1)
        print(f"Found {len(earnings_data)} earnings items:")
        for item in earnings_data:
            print(f"  {item['category']}: {item['hours']}h, ${item['amount']}, YTD ${item['ytd']}")
        
        # Test tax deductions extraction
        print(f"\n--- TAX DEDUCTIONS EXTRACTION ---")
        tax_data = extract_tax_deductions_data_pdfplumber(text, page_num=1)
        print(f"Found {len(tax_data)} tax deduction items:")
        for item in tax_data:
            print(f"  {item['category']}: ${item['amount']}, YTD ${item['ytd']}")
        
        # Test deductions extraction
        print(f"\n--- DEDUCTIONS EXTRACTION ---")
        deductions_data = extract_deductions_data_pdfplumber(text, page_num=1)
        print(f"Found {len(deductions_data)} deduction items:")
        for item in deductions_data:
            print(f"  {item['category']}: ${item['amount']}, YTD ${item['ytd']}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Earnings: {len(earnings_data)} items")
        print(f"Tax Deductions: {len(tax_data)} items")
        print(f"Deductions: {len(deductions_data)} items")
        print(f"Total extracted items: {len(earnings_data) + len(tax_data) + len(deductions_data)}")

if __name__ == "__main__":
    test_mixed_patterns()