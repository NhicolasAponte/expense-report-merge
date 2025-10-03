#!/usr/bin/env python3
"""
Analyze pdfplumber text format and create earnings patterns based on earnings_key.csv
"""

import os
import csv
import pdfplumber
from regex_patterns.earnings_regex import extract_earnings_data

def analyze_earnings_patterns():
    """Analyze the first 5 pages to understand pdfplumber earnings format."""
    pdf_path = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
    key_path = os.path.join(os.path.dirname(__file__), "test-keys", "earnings_key.csv")
    
    # Load expected data
    expected_data = {}
    with open(key_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            page = int(row['page_number'])
            if page not in expected_data:
                expected_data[page] = []
            expected_data[page].append({
                'employee_name': row['employee_name'],
                'employee_number': row['employee_number'],
                'category': row['category'],
                'hours': float(row['hours']),
                'amount': float(row['amount']),
                'ytd': float(row['ytd'])
            })
    
    print("Analyzing earnings extraction patterns...")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(1, 6):  # First 5 pages
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            
            print(f"\nPAGE {page_num}")
            print("-" * 40)
            
            expected = expected_data.get(page_num, [])
            print(f"Expected {len(expected)} earnings items:")
            for item in expected:
                print(f"  {item['category']}: {item['hours']} hrs, ${item['amount']}, YTD ${item['ytd']}")
            
            print("\nText around earnings section:")
            lines = text.split('\n')
            earnings_start = -1
            for i, line in enumerate(lines):
                if 'EARNINGS' in line:
                    earnings_start = i
                    break
            
            if earnings_start != -1:
                for i in range(earnings_start, min(earnings_start + 10, len(lines))):
                    line = lines[i].strip()
                    print(f"  Line {i:2d}: {repr(line)}")
                    
                    # Check if this line matches any expected earnings
                    for item in expected:
                        if item['category'] in line:
                            print(f"          -> MATCHES: {item['category']}")
            
            print(f"\nCurrent extraction result:")
            current_result = extract_earnings_data(text, page_num)
            print(f"  Found {len(current_result)} items: {current_result}")

if __name__ == "__main__":
    analyze_earnings_patterns()