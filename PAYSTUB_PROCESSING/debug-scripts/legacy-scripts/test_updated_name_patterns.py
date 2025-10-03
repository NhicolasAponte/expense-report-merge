#!/usr/bin/env python3
"""
Test the updated name extraction patterns with problematic pages.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
import re

def test_updated_name_patterns():
    """Test the updated name extraction patterns"""
    
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_00-07_Paystubs.pdf")
    problematic_pages = [162, 145, 107, 96, 19]
    
    print(f"Testing updated name patterns with: {pdf_path}")
    
    # Updated patterns from the pipeline
    name_date_pattern = r'^([A-Za-z][A-Za-z\s\.\'\-,]+?)\s+(?:\d+\s+)?(\d{1,2}/\d{1,2}/\d{4})$'
    name_date_fallback_pattern = r'^([A-Za-z][A-Za-z\s\.0\'\-,]+?)\s+(?:\d+\s+)?(\d{1,2}/\d{1,2}/\d{4})$'
    
    with pdfplumber.open(pdf_path) as pdf:
        successful_extractions = 0
        fallback_extractions = 0
        failed_extractions = 0
        
        for page_num in problematic_pages:
            if page_num > len(pdf.pages):
                print(f"Page {page_num} doesn't exist")
                continue
                
            page = pdf.pages[page_num - 1]  # Convert to 0-indexed
            text = page.extract_text()
            
            if not text:
                print(f"Page {page_num}: No text found")
                continue
                
            lines = text.split('\n')
            page_extracted = False
            
            print(f"\n=== PAGE {page_num} TEST ===")
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Try primary pattern
                match = re.match(name_date_pattern, line_stripped)
                if match:
                    candidate_name = match.group(1).strip()
                    if len(candidate_name) >= 3 and ' ' in candidate_name:
                        print(f"✓ PRIMARY pattern matched")
                        print(f"    Line {i}: '{line_stripped}'")
                        print(f"    Name: '{candidate_name}'")
                        print(f"    Date: '{match.group(2)}'")
                        successful_extractions += 1
                        page_extracted = True
                        break
                
                # Try fallback pattern
                if not page_extracted:
                    fallback_match = re.match(name_date_fallback_pattern, line_stripped)
                    if fallback_match:
                        candidate_name = fallback_match.group(1).strip()
                        # Clean up OCR errors: 0. -> O.
                        candidate_name_cleaned = re.sub(r'\\b0\\.', 'O.', candidate_name)
                        
                        if len(candidate_name_cleaned) >= 3 and ' ' in candidate_name_cleaned:
                            print(f"⚠ FALLBACK pattern matched (OCR correction)")
                            print(f"    Line {i}: '{line_stripped}'")
                            print(f"    Name (raw): '{candidate_name}'")
                            print(f"    Name (cleaned): '{candidate_name_cleaned}'")
                            print(f"    Date: '{fallback_match.group(2)}'")
                            fallback_extractions += 1
                            page_extracted = True
                            break
            
            if not page_extracted:
                print(f"✗ No name extracted")
                failed_extractions += 1
        
        print(f"\n=== SUMMARY ===")
        print(f"Successful extractions (primary pattern): {successful_extractions}")
        print(f"Fallback extractions (OCR correction): {fallback_extractions}")
        print(f"Failed extractions: {failed_extractions}")
        print(f"Total pages tested: {len(problematic_pages)}")

if __name__ == "__main__":
    test_updated_name_patterns()