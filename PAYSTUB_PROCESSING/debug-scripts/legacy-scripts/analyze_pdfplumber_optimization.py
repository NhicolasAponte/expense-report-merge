#!/usr/bin/env python3
"""
Comprehensive analysis of pdfplumber text output vs expected data
from updated earnings_key.csv for first 10 pages.
"""

import os
import csv
import pdfplumber
from regex_patterns.employee_regex import extract_employee_data_patterns
from regex_patterns.earnings_regex import extract_earnings_data

def analyze_pdfplumber_patterns():
    """Analyze pdfplumber text patterns for optimization opportunities."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    key_path = os.path.join(os.path.dirname(__file__), "test-keys", "earnings_key.csv")
    
    # Load expected data from updated key file
    expected_data = {}
    with open(key_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            page = int(row['page_number'])
            if page not in expected_data:
                expected_data[page] = {
                    'employee_name': row['employee_name'],
                    'employee_number': row['employee_number'],
                    'period_end': row['period_end'],
                    'earnings': []
                }
            expected_data[page]['earnings'].append({
                'category': row['category'],
                'hours': row['hours'],
                'amount': row['amount'],
                'ytd': row['ytd']
            })
    
    print("COMPREHENSIVE PDFPLUMBER PATTERN ANALYSIS")
    print("=" * 70)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(1, 11):  # First 10 pages
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            
            print(f"\nPAGE {page_num}")
            print("-" * 50)
            
            expected = expected_data.get(page_num, {})
            print(f"Expected Employee: {expected.get('employee_name', 'N/A')} ({expected.get('employee_number', 'N/A')})")
            print(f"Expected Period End: {expected.get('period_end', 'N/A')}")
            print(f"Expected Earnings: {len(expected.get('earnings', []))} items")
            
            # Current extraction results
            current_employee = extract_employee_data_patterns(text, page_num)
            current_earnings = extract_earnings_data(text, page_num)
            
            print(f"\nCurrent Extraction:")
            print(f"  Employee: {current_employee.get('employee_name', '')} ({current_employee.get('employee_number', '')})")
            print(f"  Period End: {current_employee.get('period_end', '')}")
            print(f"  Earnings: {len(current_earnings)} items")
            
            # Identify issues
            issues = []
            if current_employee.get('employee_name', '') != expected.get('employee_name', ''):
                issues.append(f"Name mismatch: got '{current_employee.get('employee_name', '')}', expected '{expected.get('employee_name', '')}'")
            if current_employee.get('employee_number', '') != expected.get('employee_number', ''):
                issues.append(f"Number mismatch: got '{current_employee.get('employee_number', '')}', expected '{expected.get('employee_number', '')}'")
            if len(current_earnings) != len(expected.get('earnings', [])):
                issues.append(f"Earnings count mismatch: got {len(current_earnings)}, expected {len(expected.get('earnings', []))}")
            
            if issues:
                print(f"\n  ⚠️  ISSUES FOUND:")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print(f"\n  ✅ All data matches expected values")
            
            # Show raw text analysis for problematic pages
            if issues:
                print(f"\n  📝 Raw Text Analysis:")
                lines = text.split('\n')
                
                # Show employee data section (first 15 lines)
                print(f"    Employee Data Section (lines 1-15):")
                for i, line in enumerate(lines[:15], 1):
                    print(f"      {i:2d}: {repr(line)}")
                
                # Show earnings section
                earnings_start = -1
                for i, line in enumerate(lines):
                    if 'EARNINGS' in line:
                        earnings_start = i
                        break
                
                if earnings_start != -1:
                    print(f"    Earnings Section (lines {earnings_start+1}-{earnings_start+10}):")
                    for i in range(earnings_start, min(earnings_start + 10, len(lines))):
                        print(f"      {i+1:2d}: {repr(lines[i])}")
            
            print()

if __name__ == "__main__":
    analyze_pdfplumber_patterns()