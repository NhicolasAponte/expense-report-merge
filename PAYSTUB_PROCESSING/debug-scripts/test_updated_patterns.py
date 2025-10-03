#!/usr/bin/env python3
"""
Test the updated employee number extraction patterns with the new PDF.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
import re

def test_updated_patterns():
    """Test the updated employee extraction patterns"""
    
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_00-07_Paystubs.pdf")
    
    print(f"Testing updated patterns with: {pdf_path}")
    
    # Updated patterns from the pipeline
    data_line_pattern = r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
    data_line_fallback_pattern = r'^([o0]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        successful_extractions = 0
        fallback_extractions = 0
        failed_extractions = 0
        
        # Test first 10 pages
        for page_num in range(min(10, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
                
            lines = text.split('\n')
            page_extracted = False
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Try primary pattern
                match = re.match(data_line_pattern, line_stripped)
                if match:
                    print(f"✓ Page {page_num + 1}: PRIMARY pattern matched")
                    print(f"    Employee #: '{match.group(1)}'")
                    print(f"    Pay Rate: '{match.group(2)}'")
                    print(f"    Period End: '{match.group(3)}'")
                    print(f"    Stub #: '{match.group(4)}'")
                    print(f"    Raw line: '{line_stripped}'")
                    successful_extractions += 1
                    page_extracted = True
                    break
                
                # Try fallback pattern
                fallback_match = re.match(data_line_fallback_pattern, line_stripped, re.IGNORECASE)
                if fallback_match:
                    emp_num = fallback_match.group(1)
                    emp_num_corrected = re.sub(r'^[o0]{2}-', '00-', emp_num, flags=re.IGNORECASE)
                    
                    print(f"⚠ Page {page_num + 1}: FALLBACK pattern matched (OCR correction)")
                    print(f"    Employee # (OCR): '{fallback_match.group(1)}'")
                    print(f"    Employee # (corrected): '{emp_num_corrected}'")
                    print(f"    Pay Rate: '{fallback_match.group(2)}'")
                    print(f"    Period End: '{fallback_match.group(3)}'")
                    print(f"    Stub #: '{fallback_match.group(4)}'")
                    print(f"    Raw line: '{line_stripped}'")
                    fallback_extractions += 1
                    page_extracted = True
                    break
            
            if not page_extracted:
                print(f"✗ Page {page_num + 1}: No employee data extracted")
                # Show any lines that might contain employee info for debugging
                for i, line in enumerate(lines):
                    if re.search(r'Employee Number|[0-9]{2}-[A-Z]|[o0]{2}-[A-Z]', line):
                        print(f"    Debug line {i+1}: '{line.strip()}'")
                failed_extractions += 1
        
        print(f"\n=== SUMMARY ===")
        print(f"Successful extractions (primary pattern): {successful_extractions}")
        print(f"Fallback extractions (OCR correction): {fallback_extractions}")
        print(f"Failed extractions: {failed_extractions}")
        print(f"Total pages tested: {min(10, len(pdf.pages))}")

if __name__ == "__main__":
    test_updated_patterns()