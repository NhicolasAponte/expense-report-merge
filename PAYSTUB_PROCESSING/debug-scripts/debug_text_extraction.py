#!/usr/bin/env python3
"""
Debug script to compare text extraction between PyPDF2 and pdfplumber
"""

import os
import pdfplumber
import PyPDF2
from regex_patterns.employee_regex import extract_employee_data_patterns

def compare_text_extraction():
    """Compare text extraction from both libraries."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    
    print("Comparing PyPDF2 vs pdfplumber text extraction for page 1...")
    print("=" * 60)
    
    # PyPDF2 extraction
    print("PyPDF2 extraction:")
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        page1_pypdf2 = reader.pages[0]
        text_pypdf2 = page1_pypdf2.extract_text()
        print(f"Text length: {len(text_pypdf2)}")
        print("First 500 characters:")
        print(repr(text_pypdf2[:500]))
        print()
        
        # Test employee extraction with PyPDF2 text
        employee_data_pypdf2 = extract_employee_data_patterns(text_pypdf2, 1)
        print("Employee data from PyPDF2:")
        for key, value in employee_data_pypdf2.items():
            print(f"  {key}: {repr(value)}")
    
    print("\n" + "=" * 60)
    
    # pdfplumber extraction
    print("pdfplumber extraction:")
    with pdfplumber.open(pdf_path) as pdf:
        page1_pdfplumber = pdf.pages[0]
        text_pdfplumber = page1_pdfplumber.extract_text()
        print(f"Text length: {len(text_pdfplumber)}")
        print("First 500 characters:")
        print(repr(text_pdfplumber[:500]))
        print()
        
        # Test employee extraction with pdfplumber text
        employee_data_pdfplumber = extract_employee_data_patterns(text_pdfplumber, 1)
        print("Employee data from pdfplumber:")
        for key, value in employee_data_pdfplumber.items():
            print(f"  {key}: {repr(value)}")
    
    print("\n" + "=" * 60)
    print("Comparison:")
    print(f"PyPDF2 text == pdfplumber text: {text_pypdf2 == text_pdfplumber}")
    print(f"PyPDF2 length: {len(text_pypdf2)}")
    print(f"pdfplumber length: {len(text_pdfplumber)}")
    
    # Show differences in first few lines
    pypdf2_lines = text_pypdf2.split('\n')[:10]
    pdfplumber_lines = text_pdfplumber.split('\n')[:10]
    
    print("\nFirst 10 lines comparison:")
    for i, (p2_line, pp_line) in enumerate(zip(pypdf2_lines, pdfplumber_lines)):
        if p2_line != pp_line:
            print(f"Line {i+1} differs:")
            print(f"  PyPDF2:     {repr(p2_line)}")
            print(f"  pdfplumber: {repr(pp_line)}")

if __name__ == "__main__":
    compare_text_extraction()