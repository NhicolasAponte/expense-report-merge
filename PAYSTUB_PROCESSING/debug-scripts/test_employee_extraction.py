#!/usr/bin/env python3
"""
Test employee data extraction with pdfplumber format
"""

import os
import pdfplumber
from regex_patterns.employee_regex import extract_employee_data_patterns

def test_employee_extraction():
    """Test employee data extraction on page 1."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("Testing employee data extraction with pdfplumber format...")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        text = page1.extract_text()
        
        print(f"Text length: {len(text)}")
        print("Text preview (first 800 characters):")
        print(text[:800])
        print()
        
        # Test centralized patterns
        print("Testing centralized patterns:")
        employee_data = extract_employee_data_patterns(text, 1)
        for key, value in employee_data.items():
            print(f"  {key}: '{value}'")
        print()
        
        # Test pdfplumber-specific patterns
        print("Testing pdfplumber-specific patterns:")
        import re
        
        lines = text.split('\n')
        
        # Pattern 1: Name and date on same line like "Dakota J. Ausmus 9/19/2025"
        name_date_pattern = r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
        
        # Pattern 2: Data line like "22-ADJ ···-··-8819 20.50 HW 9/13/2025 D000123144"
        data_line_pattern = r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·\-\s]+\d+[·\-\s]*(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
        
        print("Lines analysis:")
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            print(f"Line {i+1:2d}: {repr(line)}")
            
            # Check name pattern
            match = re.match(name_date_pattern, line)
            if match:
                print(f"         -> NAME MATCH: '{match.group(1)}', DATE: '{match.group(2)}'")
            
            # Check data pattern
            match = re.match(data_line_pattern, line)
            if match:
                print(f"         -> DATA MATCH: EMP='{match.group(1)}', RATE='{match.group(2)}', DATE='{match.group(3)}', STUB='{match.group(4)}'")

if __name__ == "__main__":
    test_employee_extraction()