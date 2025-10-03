#!/usr/bin/env python3
"""
[DEPRECATED] Paystub Amount Extraction Script

DEPRECATED: This script uses PyPDF2 for text extraction. Use paystub_pipeline.py instead,
which uses pdfplumber for better text extraction and structured layout handling.
"""

import os
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader
# Import the centralized employee regex patterns
from regex_patterns.employee_regex import extract_employee_data_patterns
# Import the centralized earnings regex patterns
from regex_patterns.earnings_regex import extract_earnings_data

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_FILE = os.path.join(TEST_FILES_DIR, "All_20_Paystubs.pdf")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "result-files", "earnings.csv")

def extract_employee_data_from_page(text):
    """Extract employee data from a single page of text using centralized regex patterns"""
    # Use the centralized extraction function
    employee_data = extract_employee_data_patterns(text, page_num=1)
    
    # Convert to the expected format for this function (only the fields this script needs)
    data = {
        'employee_name': employee_data.get('employee_name', ''),
        'employee_number': employee_data.get('employee_number', ''),
        'period_end': employee_data.get('period_end', '')
    }
    
    return data

def extract_earnings_from_page(text, filename, page_num):
    """Extract earnings data from a single page of text using centralized patterns"""
    # Extract employee data for this page
    employee_data = extract_employee_data_from_page(text)
    
    # Use centralized earnings extraction
    earnings_data = extract_earnings_data(text, page_num)
    
    if not earnings_data:
        print(f"   WARNING Page {page_num}: No earnings data found")
        return []
    
    print(f"   Categories: Found {len(earnings_data)} categories: {[item['category'] for item in earnings_data]}")
    
    # Convert to the format expected by this script
    page_earnings = []
    for item in earnings_data:
        earnings_record = {
            'filename': filename,
            'page_number': page_num,
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end'],
            'category': item['category'],
            'hours': item['hours'],
            'amount': item['amount'],
            'ytd': item['ytd']
        }
        page_earnings.append(earnings_record)
        print(f"   {item['category']}: Hours={item['hours']}, Amount={item['amount']}, YTD={item['ytd']}")
    
    # Show employee data extracted for this page
    if page_earnings:
        print(f"   Employee: {employee_data['employee_name']}")
        print(f"   Employee #: {employee_data['employee_number']}")
        print(f"   Period End: {employee_data['period_end']}")
    
    return page_earnings

def extract_all_earnings(pdf_path):
    """Extract earnings data from all pages of the PDF"""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return []
        
        filename = os.path.basename(pdf_path)
        all_earnings = []
        
        print(f"Processing {filename} ({len(reader.pages)} pages)")
        
        # Process each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                print(f"   WARNING Page {page_num}: No text found")
                continue
            
            # Extract earnings from this page
            page_earnings = extract_earnings_from_page(text, filename, page_num)
            
            if page_earnings:
                all_earnings.extend(page_earnings)
                print(f"   SUCCESS Page {page_num}: {len(page_earnings)} earnings records extracted")
            else:
                print(f"   WARNING Page {page_num}: No earnings data found")
        
        return all_earnings
        
    except Exception as e:
        print(f"ERROR processing {pdf_path}: {str(e)}")
        return []

def export_earnings_to_csv(earnings_data, output_file):
    """Export earnings data to CSV file"""
    if not earnings_data:
        print("ERROR No earnings data to export.")
        return
    
    # CSV headers
    headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'hours', 'amount', 'ytd']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for record in earnings_data:
                writer.writerow(record)
        
        print(f"SUCCESS Earnings data exported to: {output_file}")
        print(f"Records exported: {len(earnings_data)}")
        
        # Show summary statistics
        categories = set(record['category'] for record in earnings_data)
        pages = set(record['page_number'] for record in earnings_data)
        
        print(f"Summary:")
        print(f"   Pages processed: {len(pages)}")
        print(f"   Unique categories: {len(categories)}")
        print(f"   Categories found: {sorted(categories)}")
        
    except Exception as e:
        print(f"ERROR writing CSV file: {str(e)}")

def main():
    """Main function to process the PDF and export earnings data"""
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR Input file not found: {INPUT_FILE}")
        return
    
    print(f"Extracting earnings data from: {INPUT_FILE}")
    
    # Extract all earnings data
    earnings_data = extract_all_earnings(INPUT_FILE)
    
    if earnings_data:
        # Export to CSV
        export_earnings_to_csv(earnings_data, OUTPUT_CSV)
        print(f"\nProcessing complete!")
        print(f"   📁 CSV file location: {OUTPUT_CSV}")
    else:
        print("ERROR No earnings data found to export.")

if __name__ == "__main__":
    main()
