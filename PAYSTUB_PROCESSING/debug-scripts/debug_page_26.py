#!/usr/bin/env python3
"""
Debug script to analyze page 26 earnings extraction issues.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from regex_patterns.earnings_regex import extract_earnings_data_pdfplumber
from common_utils import get_pdf_path
import pdfplumber
import re

def debug_page_26_earnings():
    """Debug why page 26 is missing 4 earnings entries"""
    
    # Get the PDF file
    pdf_path = get_pdf_path()
    print(f"Debugging page 26 earnings extraction with: {pdf_path}")
    
    # Extract page 26 (0-indexed = page 25)
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < 26:
            print("ERROR: PDF has fewer than 26 pages")
            return
            
        page = pdf.pages[25]  # Page 26 (0-indexed)
        text = page.extract_text()
        
        if not text:
            print("ERROR: No text found on page 26")
            return
        
        print(f"\n=== PAGE 26 RAW TEXT ANALYSIS ===")
        
        # Show raw text
        lines = text.split('\n')
        print(f"Total lines: {len(lines)}")
        
        print(f"\n--- All Lines ---")
        for i, line in enumerate(lines):
            print(f"Line {i+1}: '{line}'")
        
        # Find earnings section
        print(f"\n--- EARNINGS SECTION DETECTION ---")
        earnings_start = -1
        earnings_end = -1
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if ('•••' in line or '***' in line or ('***' in line and '•••' in line) or ('•••' in line and '***' in line)) and 'EARNINGS' in line:
                print(f"EARNINGS START found at line {i+1}: '{line_stripped}'")
                earnings_start = i + 1
            elif earnings_start != -1 and (('•••' in line or '***' in line or ('***' in line and '•••' in line) or ('•••' in line and '***' in line)) and ('TAX' in line or 'DEDUCTIONS' in line)):
                print(f"EARNINGS END found at line {i+1}: '{line_stripped}'")
                earnings_end = i
                break
        
        if earnings_start == -1:
            print("ERROR: No earnings section start found!")
            return
        
        if earnings_end == -1:
            earnings_end = len(lines)
            print(f"EARNINGS END defaulted to end of page (line {earnings_end})")
        
        print(f"\nEarnings section: Lines {earnings_start+1} to {earnings_end}")
        
        # Show earnings section content
        print(f"\n--- EARNINGS SECTION CONTENT ---")
        for i in range(earnings_start, earnings_end):
            if i < len(lines):
                print(f"Line {i+1}: '{lines[i]}'")
        
        # Test our current regex patterns
        print(f"\n--- CURRENT REGEX EXTRACTION ---")
        earnings_data = extract_earnings_data_pdfplumber(text, page_num=26)
        print(f"Found {len(earnings_data)} earnings items:")
        for item in earnings_data:
            print(f"  {item['category']}: {item['hours']}h, ${item['amount']}, YTD ${item['ytd']}")
        
        # Test each line in earnings section against our patterns
        print(f"\n--- PATTERN MATCHING ANALYSIS ---")
        pdfplumber_pattern = r'^([A-Za-z0-9][A-Za-z\s/\-\.&\(\)0-9\+]+?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)$'
        
        for i in range(earnings_start, earnings_end):
            if i < len(lines):
                line = lines[i].strip()
                if line and not any(char in line for char in ['•', '***', 'Amount', 'Hours', 'YTD']):
                    match = re.match(pdfplumber_pattern, line)
                    if match:
                        print(f"✓ MATCHED Line {i+1}: '{line}'")
                        print(f"    Category: '{match.group(1)}'")
                        print(f"    Hours: '{match.group(2)}'")
                        print(f"    Amount: '{match.group(3)}'")
                        print(f"    YTD: '{match.group(4)}'")
                    else:
                        print(f"✗ NOT MATCHED Line {i+1}: '{line}'")
                        # Try to understand why it didn't match
                        parts = line.split()
                        if len(parts) >= 4:
                            print(f"    Parts: {parts}")
                            print(f"    Expected pattern: Category Hours Amount YTD")
        
        # Expected vs Actual comparison
        print(f"\n--- EXPECTED VS ACTUAL ---")
        expected_categories = [
            "Holiday", "OT - Loader", "Loaders", "Metal", "Metal-OT", 
            "Paid Time Off", "Paid Time Off Payout", "2/700", "OT 2/700", "8/900", "OT 8/900"
        ]
        actual_categories = [item['category'] for item in earnings_data]
        
        print(f"Expected categories ({len(expected_categories)}): {expected_categories}")
        print(f"Actual categories ({len(actual_categories)}): {actual_categories}")
        
        missing = set(expected_categories) - set(actual_categories)
        if missing:
            print(f"Missing categories: {list(missing)}")
        else:
            print("No missing categories found!")

if __name__ == "__main__":
    debug_page_26_earnings()