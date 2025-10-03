#!/usr/bin/env python3
"""
Analyze page 45 tax deductions section boundary issues
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
from regex_patterns.deductions_regex import extract_tax_deductions_data, extract_tax_deductions_data_pdfplumber

def analyze_page_45_sections(pdf_path=None):
    """Analyze section boundaries on page 45 where tax deductions are incorrectly including other sections."""
    
    if pdf_path is None:
        pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("ANALYZING PAGE 45 SECTION BOUNDARIES")
    print("=" * 70)
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[44]  # 0-indexed, so page 45 is index 44
        text = page.extract_text()
        
        # Show raw text with line numbers
        lines = text.split('\n')
        print("Raw text lines:")
        for i, line in enumerate(lines):
            marker = ""
            if "TAX DEDUCTIONS" in line:
                marker = " <-- TAX DEDUCTIONS START"
            elif "DEDUCTIONS" in line and "TAX" not in line:
                marker = " <-- DEDUCTIONS START"
            elif "DIRECT DEPOSITS" in line:
                marker = " <-- DIRECT DEPOSITS START"
            elif "Earnings" in line or "earnings" in line:
                marker = " <-- EARNINGS SECTION"
            elif "Net Earnings" in line:
                marker = " <-- NET EARNINGS"
                
            print(f"{i+1:2d}: '{line}'{marker}")
        
        print(f"\nCurrent TAX DEDUCTIONS extraction:")
        tax_deductions = extract_tax_deductions_data(text, 45)
        print(f"Found {len(tax_deductions)} items:")
        for d in tax_deductions:
            print(f"  {d['category']} | {d['amount']} | {d['ytd']}")
        
        print(f"\nPdfplumber-specific TAX DEDUCTIONS extraction:")
        pdfplumber_tax_deductions = extract_tax_deductions_data_pdfplumber(text, 45)
        print(f"Found {len(pdfplumber_tax_deductions)} items:")
        for d in pdfplumber_tax_deductions:
            print(f"  {d['category']} | {d['amount']} | {d['ytd']}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    analyze_page_45_sections()