#!/usr/bin/env python3
"""
Debug script to analyze page 1 specifically to understand why earnings are not being extracted.
"""

import pdfplumber
import sys
import os

# Add the regex_patterns directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'regex_patterns'))

from earnings_regex import extract_earnings_data_pdfplumber
from deductions_regex import extract_tax_deductions_data_pdfplumber, extract_deductions_data_pdfplumber
from common_utils import get_pdf_path

def analyze_page_1():
    """Analyze page 1 specifically to understand why earnings are missing."""
    
    pdf_path = get_pdf_path()
    
    print("ANALYZING PAGE 1 CONTENT")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # Page 1 (0-indexed)
        text = page.extract_text()
        
        print("Raw text from page 1:")
        print("-" * 40)
        lines = text.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:2}: '{line}'")
        
        print("\n" + "=" * 60)
        print("SECTION ANALYSIS")
        print("=" * 60)
        
        # Look for section markers
        earnings_found = False
        tax_deductions_found = False
        deductions_found = False
        
        for i, line in enumerate(lines, 1):
            if 'EARNINGS' in line.upper():
                print(f"EARNINGS section marker at line {i}: '{line}'")
                earnings_found = True
            elif 'TAX DEDUCTIONS' in line.upper():
                print(f"TAX DEDUCTIONS section marker at line {i}: '{line}'")
                tax_deductions_found = True
            elif 'DEDUCTIONS' in line.upper() and 'TAX' not in line.upper():
                print(f"DEDUCTIONS section marker at line {i}: '{line}'")
                deductions_found = True
        
        print(f"\nSection markers found:")
        print(f"  EARNINGS: {earnings_found}")
        print(f"  TAX DEDUCTIONS: {tax_deductions_found}")
        print(f"  DEDUCTIONS: {deductions_found}")
        
        print("\n" + "=" * 60)
        print("EXTRACTION TESTING")
        print("=" * 60)
        
        # Test each extraction function
        print("Testing earnings extraction:")
        earnings_data = extract_earnings_data_pdfplumber(text)
        print(f"  Found {len(earnings_data)} earnings items:")
        for item in earnings_data:
            print(f"    {item['category']} | {item['hours']} | {item['amount']} | {item['ytd']}")
        
        print("\nTesting tax deductions extraction:")
        tax_data = extract_tax_deductions_data_pdfplumber(text)
        print(f"  Found {len(tax_data)} tax deductions items:")
        for item in tax_data:
            print(f"    {item['category']} | {item['amount']} | {item['ytd']}")
        
        print("\nTesting deductions extraction:")
        deductions_data = extract_deductions_data_pdfplumber(text)
        print(f"  Found {len(deductions_data)} deductions items:")
        for item in deductions_data:
            print(f"    {item['category']} | {item['amount']} | {item['ytd']}")
        
        print("\n" + "=" * 60)
        print("MANUAL EARNINGS SECTION SEARCH")
        print("=" * 60)
        
        # Manually look for earnings section boundaries
        earnings_start = -1
        earnings_end = -1
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Look for earnings section start - both bullet and asterisk formats
            if ('•••EARNINGS•••' in line_stripped or '••• EARNINGS •••' in line_stripped or 
                '***EARNINGS***' in line_stripped or '*** EARNINGS ***' in line_stripped):
                earnings_start = i
                print(f"Found earnings start at line {i+1}: '{line_stripped}'")
            elif earnings_start != -1 and ('TAX DEDUCTIONS' in line_stripped or 
                                         ('***' in line_stripped and 'DEDUCTIONS' in line_stripped) or
                                         ('•••' in line_stripped and 'DEDUCTIONS' in line_stripped)):
                earnings_end = i
                print(f"Found earnings end at line {i+1}: '{line_stripped}'")
                break
        
        if earnings_start != -1:
            if earnings_end == -1:
                earnings_end = len(lines)
            
            print(f"\nEarnings section content (lines {earnings_start+2} to {earnings_end}):")
            for i in range(earnings_start + 1, earnings_end):
                line = lines[i].strip()
                if line:
                    print(f"  {i+1:2}: '{line}'")
        else:
            print("\nNo earnings section found with expected markers!")
            
            # Look for any line containing just "EARNINGS"
            for i, line in enumerate(lines, 1):
                if 'EARNINGS' in line.upper():
                    print(f"Found 'EARNINGS' at line {i}: '{line}'")

if __name__ == "__main__":
    analyze_page_1()