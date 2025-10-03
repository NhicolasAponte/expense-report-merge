#!/usr/bin/env python3
"""
Quick script to regenerate earnings.csv with the fix.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from common_utils import get_pdf_path, setup_output_directory, get_pdf_filename_without_extension
from regex_patterns.earnings_regex import extract_earnings_data
import pdfplumber
import csv

def regenerate_earnings_csv():
    """Regenerate just the earnings CSV file"""
    
    pdf_path = get_pdf_path()
    output_dir = setup_output_directory()
    filename = get_pdf_filename_without_extension(pdf_path)
    
    print(f"Regenerating earnings CSV from: {pdf_path}")
    
    all_earnings = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(1, len(pdf.pages) + 1):
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            
            if text:
                earnings_data = extract_earnings_data(text, page_num)
                
                # Add page and file info
                for item in earnings_data:
                    item['filename'] = f"{filename}.pdf"
                    item['page_number'] = str(page_num)
                    item['employee_name'] = ""  # Will be filled by main pipeline
                    item['employee_number'] = ""
                    item['period_end'] = ""
                
                all_earnings.extend(earnings_data)
                
                if page_num == 26:
                    print(f"Page 26: Found {len(earnings_data)} earnings items")
    
    # Write CSV
    output_path = os.path.join(output_dir, "earnings_fixed.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'hours', 'amount', 'ytd']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_earnings)
    
    print(f"✅ Generated: {output_path}")
    print(f"Total earnings records: {len(all_earnings)}")
    
    # Show page 26 data
    page_26_data = [item for item in all_earnings if item['page_number'] == '26']
    print(f"\nPage 26 earnings ({len(page_26_data)} items):")
    for item in page_26_data:
        print(f"  {item['category']}: {item['hours']}h, ${item['amount']}, YTD ${item['ytd']}")

if __name__ == "__main__":
    regenerate_earnings_csv()