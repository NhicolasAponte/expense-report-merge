#!/usr/bin/env python3
"""
Analyze specific pages with employee name extraction issues.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
import re

def analyze_problematic_pages():
    """Analyze pages 162, 145, 107, 96, 19 for employee name extraction issues"""
    
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_00-07_Paystubs.pdf")
    problematic_pages = [162, 145, 107, 96, 19]
    
    print(f"Analyzing problematic pages from: {pdf_path}")
    
    # Current name extraction pattern from pipeline
    name_date_pattern = r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in problematic_pages:
            if page_num > len(pdf.pages):
                print(f"Page {page_num} doesn't exist (PDF has {len(pdf.pages)} pages)")
                continue
                
            page = pdf.pages[page_num - 1]  # Convert to 0-indexed
            text = page.extract_text()
            
            if not text:
                print(f"Page {page_num}: No text found")
                continue
                
            print(f"\n{'='*60}")
            print(f"PAGE {page_num} ANALYSIS")
            print(f"{'='*60}")
            
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}")
            
            # Show all lines for analysis
            print(f"\n--- ALL LINES ---")
            for i, line in enumerate(lines, 1):
                print(f"Line {i:2d}: '{line}'")
            
            # Test current name pattern
            print(f"\n--- CURRENT NAME PATTERN TESTING ---")
            print(f"Pattern: {name_date_pattern}")
            
            found_name = False
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                match = re.match(name_date_pattern, line_stripped)
                if match:
                    print(f"✓ MATCHED Line {i}: '{line_stripped}'")
                    print(f"    Name: '{match.group(1)}'")
                    print(f"    Date: '{match.group(2)}'")
                    found_name = True
                    break
            
            if not found_name:
                print("✗ No name matches found with current pattern")
                
                # Look for potential name candidates
                print(f"\n--- POTENTIAL NAME CANDIDATES ---")
                
                # Look for lines that might contain names
                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    # Skip obvious non-name lines
                    if not line_stripped or len(line_stripped) < 3:
                        continue
                    if re.search(r'Manko|Window|Systems|Hayes|Box|Manhattan|Employee|Number|Social|Security|Pay|Rate|Period|End|Stub|Hours|Amount|YTD|EARNINGS|DEDUCTIONS|DIRECT|DEPOSITS', line_stripped, re.IGNORECASE):
                        continue
                    if re.search(r'^\d+$|^[^A-Za-z]*$|^\d{2}-[A-Z]|^D\d+', line_stripped):
                        continue
                    
                    # Look for name-like patterns
                    if re.search(r'^[A-Za-z][A-Za-z\s\.\'\-,]{2,}', line_stripped):
                        print(f"Candidate Line {i}: '{line_stripped}'")
                        
                        # Test various name patterns
                        patterns_to_test = [
                            (r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$', 'Name + Date'),
                            (r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)$', 'Name only'),
                            (r'^([A-Za-z][A-Za-z\s\.\'\-,]{2,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$', 'Relaxed Name + Date'),
                            (r'^([A-Za-z][A-Za-z\s\.\'\-,]{2,}?)$', 'Relaxed Name only'),
                        ]
                        
                        for pattern, desc in patterns_to_test:
                            test_match = re.match(pattern, line_stripped)
                            if test_match:
                                print(f"    ✓ {desc}: '{test_match.group(1)}'")
                                if test_match.lastindex and test_match.lastindex > 1:
                                    print(f"        Date: '{test_match.group(2)}'")
            
            # Look for employee data line
            print(f"\n--- EMPLOYEE DATA LINE ---")
            data_line_pattern = r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                match = re.match(data_line_pattern, line_stripped)
                if match:
                    print(f"✓ Employee Data Line {i}: '{line_stripped}'")
                    print(f"    Employee #: '{match.group(1)}'")
                    print(f"    Pay Rate: '{match.group(2)}'")
                    print(f"    Period End: '{match.group(3)}'")
                    print(f"    Stub #: '{match.group(4)}'")
                    break

if __name__ == "__main__":
    analyze_problematic_pages()