import pdfplumber
import sys
import os
import argparse

# Add the regex_patterns directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'regex_patterns'))

from earnings_regex import extract_earnings_data_pdfplumber
from common_utils import get_pdf_path

def analyze_page_44(pdf_path=None):
    """Analyze page 44 specifically to understand why Mileage isn't being extracted."""
    
    pdf_path = get_pdf_path(pdf_path)
    
    print("ANALYZING PAGE 44 EARNINGS EXTRACTION")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[43]  # Page 44 (0-indexed)
        text = page.extract_text()
        
        print("Raw text from page 44:")
        print("-" * 40)
        lines = text.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:2}: '{line}'")
        
        print("\n" + "=" * 60)
        print("EARNINGS SECTION ANALYSIS")
        print("=" * 60)
        
        # Find the earnings section
        earnings_start = None
        earnings_end = None
        
        for i, line in enumerate(lines):
            if ('•••EARNINGS•••' in line or '••• EARNINGS •••' in line or 
                '***EARNINGS***' in line or '*** EARNINGS ***' in line):
                earnings_start = i
                print(f"EARNINGS section starts at line {i + 1}: '{line}'")
            elif earnings_start is not None and ('••• TAX DEDUCTIONS •••' in line or '•••TAX DEDUCTIONS•••' in line):
                earnings_end = i
                print(f"EARNINGS section ends at line {i + 1}: '{line}'")
                break
        
        if earnings_start is not None:
            if earnings_end is None:
                earnings_end = len(lines)
            
            earnings_lines = lines[earnings_start + 1:earnings_end]
            print(f"\nEarnings section content (lines {earnings_start + 2} to {earnings_end}):")
            for i, line in enumerate(earnings_lines):
                print(f"  {earnings_start + i + 2:2}: '{line}'")
            
            print("\n" + "=" * 60)
            print("TESTING REGEX EXTRACTION")
            print("=" * 60)
            
            # Test the extraction function
            earnings_data = extract_earnings_data_pdfplumber(text)
            print(f"Extracted {len(earnings_data)} earnings items:")
            for item in earnings_data:
                print(f"  {item['category']} | {item['hours']} | {item['amount']} | {item['ytd']}")
                
            # Debug the section boundaries for the function
            print(f"\nDEBUGGING pdfplumber function section detection:")
            lines = text.split('\n')
            earnings_start = -1
            earnings_end = -1
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Look for earnings section start - both bullet and asterisk formats
                if ('•••EARNINGS•••' in line_stripped or '••• EARNINGS •••' in line_stripped or 
                    '***EARNINGS***' in line_stripped or '*** EARNINGS ***' in line_stripped) and earnings_start == -1:
                    earnings_start = i
                    print(f"Found earnings start at line {i+1}: '{line_stripped}'")
                elif earnings_start != -1 and ('TAX DEDUCTIONS' in line_stripped or 
                                             ('***' in line_stripped and 'DEDUCTIONS' in line_stripped) or
                                             ('•••' in line_stripped and 'DEDUCTIONS' in line_stripped)):
                    earnings_end = i
                    print(f"Found earnings end at line {i+1}: '{line_stripped}'")
                    break
            
            print(f"Section range: lines {earnings_start+1} to {earnings_end} (content lines {earnings_start+2} to {earnings_end})")
            if earnings_start != -1 and earnings_end != -1:
                for i in range(earnings_start + 1, earnings_end):
                    line = lines[i].strip()
                    print(f"Processing line {i+1}: '{line}'")
                
            print("\n" + "=" * 60)
            print("MANUAL PATTERN TESTING")
            print("=" * 60)
            
            # Test individual patterns on each line
            import re
            
            # These are the patterns from earnings_regex.py
            patterns = [
                r'^([A-Za-z][A-Za-z0-9\s\.\-\/]*?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)$',
                r'^([A-Za-z][A-Za-z0-9\s\.\-\/]*?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)$',
                r'^([A-Za-z][A-Za-z0-9\s\.\-\/]*?)\s+([\d,]+\.?\d*)$'
            ]
            
            for line in earnings_lines:
                line = line.strip()
                if line and not line.startswith('•'):
                    print(f"\nTesting line: '{line}'")
                    for i, pattern in enumerate(patterns, 1):
                        match = re.match(pattern, line)
                        if match:
                            print(f"  Pattern {i} MATCHES: {match.groups()}")
                        else:
                            print(f"  Pattern {i} no match")
        else:
            print("No EARNINGS section found!")

def main():
    """Command-line interface for page 44 analysis."""
    parser = argparse.ArgumentParser(description="Analyze page 44 earnings extraction")
    parser.add_argument(
        "pdf_path",
        nargs="?", 
        default=None,
        help="Path to input PDF file (auto-detects from test-files/ if not provided)"
    )
    
    args = parser.parse_args()
    analyze_page_44(args.pdf_path)

if __name__ == "__main__":
    main()