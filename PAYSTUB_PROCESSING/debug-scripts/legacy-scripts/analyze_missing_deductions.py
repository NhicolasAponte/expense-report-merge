#!/usr/bin/env python3
"""
Analyze missing deductions from pages 10 and 22
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
from regex_patterns.deductions_regex import extract_deductions_data, extract_deductions_data_pdfplumber

def analyze_missing_deductions(pdf_path=None):
    """Analyze why deductions are missing from pages 10 and 22."""
    
    if pdf_path is None:
        pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("ANALYZING MISSING DEDUCTIONS")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [10, 22]:
            print(f"\nPAGE {page_num} ANALYSIS")
            print("-" * 40)
            
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            
            # Show raw text around deductions section
            lines = text.split('\n')
            print("Raw text lines:")
            for i, line in enumerate(lines):
                if i > 50:  # Limit output
                    break
                print(f"{i+1:2d}: '{line}'")
            
            print(f"\nCurrent extraction results:")
            deductions = extract_deductions_data(text, page_num)
            for d in deductions:
                print(f"  {d['category']} | {d['amount']} | {d['ytd']}")
            
            print(f"\nPdfplumber-specific extraction:")
            pdfplumber_deductions = extract_deductions_data_pdfplumber(text, page_num)
            for d in pdfplumber_deductions:
                print(f"  {d['category']} | {d['amount']} | {d['ytd']}")
            
            print("\n" + "=" * 60)

if __name__ == "__main__":
    analyze_missing_deductions()