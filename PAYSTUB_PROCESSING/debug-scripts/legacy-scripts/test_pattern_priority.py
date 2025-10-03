#!/usr/bin/env python3
"""
Quick test to verify optimized pattern prioritization.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pdfplumber
from regex_patterns.employee_regex import extract_employee_data_patterns
from regex_patterns.earnings_regex import extract_earnings_data
from regex_patterns.deductions_regex import extract_tax_deductions_data, extract_deductions_data

def test_pattern_prioritization():
    """Test that pdfplumber patterns are prioritized correctly."""
    
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("Testing Pattern Prioritization")
    print("=" * 50)
    
    with pdfplumber.open(pdf_path) as pdf:
        # Test first 3 pages
        for page_num in range(1, 4):
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            
            print(f"\nPage {page_num}:")
            
            # Test employee data extraction
            employee_data = extract_employee_data_patterns(text, page_num)
            print(f"  Employee: {employee_data.get('employee_name', 'N/A')} ({employee_data.get('employee_number', 'N/A')})")
            
            # Test earnings extraction  
            earnings = extract_earnings_data(text, page_num)
            print(f"  Earnings: {len(earnings)} items")
            
            # Test tax deductions extraction
            tax_deductions = extract_tax_deductions_data(text, page_num)
            print(f"  Tax Deductions: {len(tax_deductions)} items")
            
            # Test regular deductions extraction
            deductions = extract_deductions_data(text, page_num)
            print(f"  Deductions: {len(deductions)} items")
            
            # Check if all extractions were successful
            success = (
                employee_data.get('employee_name') and 
                employee_data.get('employee_number') and
                len(earnings) > 0 and
                len(tax_deductions) > 0
            )
            
            print(f"  Status: {'✅ SUCCESS' if success else '❌ PARTIAL'}")
    
    print("\n" + "=" * 50)
    print("Pattern prioritization test completed!")

if __name__ == "__main__":
    test_pattern_prioritization()