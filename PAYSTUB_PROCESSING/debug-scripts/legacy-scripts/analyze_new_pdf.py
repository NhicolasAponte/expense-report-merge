#!/usr/bin/env python3
"""
Analyze the new test file to identify OCR issues with employee numbers.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
import re

def analyze_new_test_file():
    """Analyze the new PDF file to find OCR issues with employee numbers"""
    
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_00-07_Paystubs.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found: {pdf_path}")
        return
    
    print(f"Analyzing new test file: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Analyze first few pages to understand the structure
        for page_num in range(min(5, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
                
            print(f"\n=== PAGE {page_num + 1} ANALYSIS ===")
            
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}")
            
            # Look for lines that might contain employee numbers
            print(f"\n--- Lines with potential employee numbers ---")
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Look for patterns that might be employee numbers
                if re.search(r'(00-|oo-|\d{2}-|[o0]{2}-)', line_stripped, re.IGNORECASE):
                    print(f"Line {i+1}: '{line_stripped}'")
                
                # Also look for the data line pattern
                if re.search(r'[\d\w]{2,}-\w+.*HW.*\d{1,2}/\d{1,2}/\d{4}.*D\d+', line_stripped):
                    print(f"Data line {i+1}: '{line_stripped}'")
            
            # Look for employee information sections
            print(f"\n--- Employee info sections ---")
            for i, line in enumerate(lines):
                if 'Employee Number' in line or 'Social Security' in line:
                    print(f"Header line {i+1}: '{line.strip()}'")
                    # Show next few lines
                    for j in range(1, 4):
                        if i + j < len(lines):
                            print(f"  +{j}: '{lines[i + j].strip()}'")
            
            # Test current extraction pattern
            print(f"\n--- Current pattern testing ---")
            data_line_pattern = r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·\-\s]+\d+[·\-\s]*(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
            
            found_matches = False
            for i, line in enumerate(lines):
                match = re.match(data_line_pattern, line.strip())
                if match:
                    found_matches = True
                    print(f"✓ MATCHED Line {i+1}: '{line.strip()}'")
                    print(f"    Employee #: '{match.group(1)}'")
                    print(f"    Pay Rate: '{match.group(2)}'")
                    print(f"    Period End: '{match.group(3)}'")
                    print(f"    Stub #: '{match.group(4)}'")
            
            if not found_matches:
                print("✗ No matches found with current pattern")
                
                # Try fallback pattern with 'oo-'
                print(f"\n--- Testing fallback pattern with 'oo-' ---")
                fallback_pattern = r'^([o0]{2}-[A-Z]+[0-9]*)\s+[·\-\s]+\d+[·\-\s]*(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
                
                for i, line in enumerate(lines):
                    match = re.match(fallback_pattern, line.strip(), re.IGNORECASE)
                    if match:
                        print(f"✓ FALLBACK MATCHED Line {i+1}: '{line.strip()}'")
                        print(f"    Employee # (OCR): '{match.group(1)}'")
                        print(f"    Employee # (corrected): '{match.group(1).replace('oo-', '00-').replace('OO-', '00-')}'")
                        print(f"    Pay Rate: '{match.group(2)}'")
                        print(f"    Period End: '{match.group(3)}'")
                        print(f"    Stub #: '{match.group(4)}'")
            
            print(f"\n" + "="*60)

if __name__ == "__main__":
    analyze_new_test_file()