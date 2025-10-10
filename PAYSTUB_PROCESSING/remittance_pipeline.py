#!/usr/bin/env python3
"""
Remittance Advice Processing Pipeline
Extracts check information, vendor details, and invoice line items from remittance PDFs.
"""

import pdfplumber
import csv
import re
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def extract_check_info(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract check information from the text, returning separate check ID and date."""
    # Look for pattern: Check: E000016062 6/23/2025
    check_pattern = r'Check:\s*([A-Z]\d+)\s+(\d{1,2}/\d{1,2}/\d{4})'
    match = re.search(check_pattern, text)
    if match:
        check_id, check_date = match.groups()
        return check_id, check_date
    return None, None


def extract_vendor_info(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract vendor information from the text, returning separate vendor number and name."""
    # Look for pattern: Vendor: 00-0000085 4D Window Specialties, LLC
    vendor_pattern = r'Vendor:\s*(\d{2}-\d{7})\s+(.+?)(?:\n|$)'
    match = re.search(vendor_pattern, text)
    if match:
        vendor_number, vendor_name = match.groups()
        # Clean up vendor name (remove extra whitespace)
        vendor_name = vendor_name.strip()
        return vendor_number, vendor_name
    return None, None


def extract_invoice_line_items(text: str) -> List[Dict[str, str]]:
    """Extract invoice line items from the text."""
    line_items = []
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    # Find the line with invoice data
    # Look for pattern: date invoice_number comment amount discount net_amount
    for line in lines:
        # Look for date pattern at start of line followed by invoice data
        # Updated pattern to handle hyphens and other characters in invoice numbers
        invoice_pattern = r'(\d{1,2}/\d{1,2}/\d{4})\s+([^\s]+)\s+.*?(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        match = re.search(invoice_pattern, line)
        
        if match:
            invoice_date, invoice_number, amount_total, discount_total, net_total = match.groups()
            line_items.append({
                'invoice_date': invoice_date,
                'invoice_number': invoice_number,
                'amount_total': amount_total,
                'discount_total': discount_total,
                'net_total': net_total
            })
    
    return line_items


def process_remittance_pdf(pdf_path: str) -> Dict:
    """Process a single remittance PDF and extract all relevant data."""
    print(f"Processing remittance PDF: {pdf_path}")
    
    extracted_data = {
        'pages': []  # Each page will have its own check_info, vendor_info, and invoice_line_items
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"  Total pages: {len(pdf.pages)}")
            
            # Process each page individually
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"  Processing page {page_num}...")
                page_text = page.extract_text(layout=True)
                
                if page_text:
                    page_data = {
                        'page_number': page_num,
                        'check_id': None,
                        'check_date': None,
                        'vendor_number': None,
                        'vendor_name': None,
                        'invoice_line_items': []
                    }
                    
                    # Extract data from this page only
                    print(f"    Extracting check information from page {page_num}...")
                    check_id, check_date = extract_check_info(page_text)
                    page_data['check_id'] = check_id
                    page_data['check_date'] = check_date
                    
                    print(f"    Extracting vendor information from page {page_num}...")
                    vendor_number, vendor_name = extract_vendor_info(page_text)
                    page_data['vendor_number'] = vendor_number
                    page_data['vendor_name'] = vendor_name
                    
                    print(f"    Extracting invoice line items from page {page_num}...")
                    page_data['invoice_line_items'] = extract_invoice_line_items(page_text)
                    
                    print(f"    Page {page_num}: Found {len(page_data['invoice_line_items'])} invoice line items")
                    if page_data['check_id'] and page_data['check_date']:
                        print(f"    Page {page_num}: Check: {page_data['check_id']} {page_data['check_date']}")
                    if page_data['vendor_number'] and page_data['vendor_name']:
                        print(f"    Page {page_num}: Vendor: {page_data['vendor_number']} {page_data['vendor_name']}")
                    
                    # Only add page data if we found some relevant information
                    if page_data['check_id'] or page_data['vendor_number'] or page_data['invoice_line_items']:
                        extracted_data['pages'].append(page_data)
            
            total_items = sum(len(page_data['invoice_line_items']) for page_data in extracted_data['pages'])
            print(f"  Total invoice line items across all pages: {total_items}")
            
    except Exception as e:
        print(f"  ERROR processing PDF: {e}")
    
    return extracted_data


def export_to_csv(data: Dict, output_dir: str = "remittance_results") -> str:
    """Export extracted remittance data to CSV with standard filename."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Always use the same filename
    output_path = os.path.join(output_dir, "remittance_data.csv")
    print(f"Exporting data to CSV: {output_path}")
    
    total_rows = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'page_number', 'check_id', 'check_date', 'vendor_number', 'vendor_name', 'invoice_date', 
            'invoice_number', 'amount_total', 'discount_total', 'net_total'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows (one per invoice line item from each page)
        for page_data in data['pages']:
            for line_item in page_data['invoice_line_items']:
                row = {
                    'page_number': page_data['page_number'],
                    'check_id': page_data['check_id'],
                    'check_date': page_data['check_date'],
                    'vendor_number': page_data['vendor_number'],
                    'vendor_name': page_data['vendor_name'],
                    **line_item
                }
                writer.writerow(row)
                total_rows += 1
        
        print(f"  Exported {total_rows} rows")
    
    return output_path


def process_all_remittance_files(input_dir: str = "test-files") -> List[Dict]:
    """Process all remittance PDF files in a directory."""
    all_data = []
    
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        return all_data
    
    # Find all PDF files that might be remittance files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    remittance_files = [f for f in pdf_files if 'AP' in f or 'remittance' in f.lower()]
    
    if not remittance_files:
        print(f"No remittance PDF files found in {input_dir}")
        print(f"Available PDF files: {pdf_files}")
        return all_data
    
    print(f"Found {len(remittance_files)} potential remittance files:")
    for f in remittance_files:
        print(f"  - {f}")
    print()
    
    for pdf_file in remittance_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        data = process_remittance_pdf(pdf_path)
        # Check if any pages have invoice data
        has_invoice_data = any(page_data['invoice_line_items'] for page_data in data['pages'])
        if has_invoice_data:  # Only include if we found invoice data
            all_data.append({
                'file_name': pdf_file,
                'data': data
            })
    
    return all_data


def export_all_to_csv(all_data: List[Dict], output_dir: str = "remittance_results") -> str:
    """Export all remittance data to a single CSV file named remittance_data.csv."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Always use the same filename
    output_path = os.path.join(output_dir, "remittance_data.csv")
    print(f"Exporting all data to CSV: {output_path}")
    
    total_rows = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'source_file', 'page_number', 'check_id', 'check_date', 'vendor_number', 'vendor_name', 'invoice_date', 
            'invoice_number', 'amount_total', 'discount_total', 'net_total'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows from all files and all pages
        for file_data in all_data:
            file_name = file_data['file_name']
            data = file_data['data']
            
            for page_data in data['pages']:
                for line_item in page_data['invoice_line_items']:
                    row = {
                        'source_file': file_name,
                        'page_number': page_data['page_number'],
                        'check_id': page_data['check_id'],
                        'check_date': page_data['check_date'],
                        'vendor_number': page_data['vendor_number'],
                        'vendor_name': page_data['vendor_name'],
                        **line_item
                    }
                    writer.writerow(row)
                    total_rows += 1
        
        print(f"  Exported {total_rows} total rows from {len(all_data)} files")
    
    return output_path


def main():
    """Main processing function."""
    print("=== REMITTANCE ADVICE PROCESSING PIPELINE ===")
    print()
    
    # Process all remittance files
    all_data = process_all_remittance_files("test-files")
    
    if not all_data:
        print("No remittance data extracted. Exiting.")
        return
    
    # Display summary of extracted data
    print("\n=== EXTRACTION SUMMARY ===")
    total_invoices = 0
    for file_data in all_data:
        file_name = file_data['file_name']
        data = file_data['data']
        
        print(f"File: {file_name}")
        
        for page_data in data['pages']:
            page_num = page_data['page_number']
            invoice_count = len(page_data['invoice_line_items'])
            total_invoices += invoice_count
            
            print(f"  Page {page_num}:")
            print(f"    Check ID: {page_data['check_id']}")
            print(f"    Check Date: {page_data['check_date']}")
            print(f"    Vendor Number: {page_data['vendor_number']}")
            print(f"    Vendor Name: {page_data['vendor_name']}")
            print(f"    Invoice Items: {invoice_count}")
            
            for i, item in enumerate(page_data['invoice_line_items'], 1):
                print(f"      {i}. {item['invoice_date']} | {item['invoice_number']} | ${item['net_total']}")
        print()
    
    print(f"TOTAL: {total_invoices} invoice line items from {len(all_data)} files")
    
    # Export to CSV - always use the same filename
    output_path = export_all_to_csv(all_data, "remittance_results")
    
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process remittance advice PDF files')
    parser.add_argument('--input', '-i', default='test-files', 
                       help='Input directory or specific PDF file (default: test-files)')
    parser.add_argument('--output', '-o', default='remittance_results', 
                       help='Output directory (default: remittance_results)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set up global verbose flag
    verbose = args.verbose
    
    if len(sys.argv) == 1:
        # No arguments provided, run with defaults
        main()
    else:
        # Custom arguments provided
        print("=== REMITTANCE ADVICE PROCESSING PIPELINE ===")
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
        print()
        
        if os.path.isfile(args.input):
            # Process single file
            data = process_remittance_pdf(args.input)
            # Check if any pages have invoice data
            has_invoice_data = any(page_data['invoice_line_items'] for page_data in data['pages'])
            if has_invoice_data:
                all_data = [{'file_name': os.path.basename(args.input), 'data': data}]
                
                # Display extracted data
                print("=== EXTRACTED DATA ===")
                for page_data in data['pages']:
                    page_num = page_data['page_number']
                    print(f"Page {page_num}:")
                    print(f"  Check ID: {page_data['check_id']}")
                    print(f"  Check Date: {page_data['check_date']}")
                    print(f"  Vendor Number: {page_data['vendor_number']}")
                    print(f"  Vendor Name: {page_data['vendor_name']}")
                    print(f"  Invoice Items: {len(page_data['invoice_line_items'])}")
                    for i, item in enumerate(page_data['invoice_line_items'], 1):
                        print(f"    {i}. {item['invoice_date']} | {item['invoice_number']} | ${item['net_total']}")
                
                # Export to CSV - always use the same filename
                output_path = export_all_to_csv(all_data, args.output)
                print(f"\nResults saved to: {output_path}")
            else:
                print("No remittance data found in the specified file.")
        else:
            # Process directory
            all_data = process_all_remittance_files(args.input)
            if all_data:
                output_path = export_all_to_csv(all_data, args.output)
                print(f"\nResults saved to: {output_path}")
            else:
                print("No remittance files found to process.")