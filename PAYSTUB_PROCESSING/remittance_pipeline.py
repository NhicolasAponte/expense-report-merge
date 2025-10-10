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


def extract_check_info(text: str) -> Optional[str]:
    """Extract check information from the text."""
    # Look for pattern: Check: E000016062 6/23/2025
    check_pattern = r'Check:\s*([A-Z]\d+)\s+(\d{1,2}/\d{1,2}/\d{4})'
    match = re.search(check_pattern, text)
    if match:
        check_number, check_date = match.groups()
        return f"{check_number} {check_date}"
    return None


def extract_vendor_info(text: str) -> Optional[str]:
    """Extract vendor information from the text."""
    # Look for pattern: Vendor: 00-0000085 4D Window Specialties, LLC
    vendor_pattern = r'Vendor:\s*(\d{2}-\d{7})\s+(.+?)(?:\n|$)'
    match = re.search(vendor_pattern, text)
    if match:
        vendor_code, vendor_name = match.groups()
        # Clean up vendor name (remove extra whitespace)
        vendor_name = vendor_name.strip()
        return f"{vendor_code} {vendor_name}"
    return None


def extract_invoice_line_items(text: str) -> List[Dict[str, str]]:
    """Extract invoice line items from the text."""
    line_items = []
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    # Find the line with invoice data
    # Look for pattern: date invoice_number comment amount discount net_amount
    for line in lines:
        # Look for date pattern at start of line followed by invoice data
        invoice_pattern = r'(\d{1,2}/\d{1,2}/\d{4})\s+(\w+)\s+.*?(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
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
        'check_info': None,
        'vendor_info': None,
        'invoice_line_items': []
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"  Total pages: {len(pdf.pages)}")
            
            # Process all pages (though typically remittance advice is single page)
            all_text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"  Processing page {page_num}...")
                page_text = page.extract_text(layout=True)
                if page_text:
                    all_text += page_text + "\n"
            
            # Extract data from combined text
            print("  Extracting check information...")
            extracted_data['check_info'] = extract_check_info(all_text)
            
            print("  Extracting vendor information...")
            extracted_data['vendor_info'] = extract_vendor_info(all_text)
            
            print("  Extracting invoice line items...")
            extracted_data['invoice_line_items'] = extract_invoice_line_items(all_text)
            
            print(f"  Found {len(extracted_data['invoice_line_items'])} invoice line items")
            
    except Exception as e:
        print(f"  ERROR processing PDF: {e}")
    
    return extracted_data


def export_to_csv(data: Dict, output_path: str) -> None:
    """Export extracted remittance data to CSV."""
    print(f"Exporting data to CSV: {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'check_info', 'vendor_info', 'invoice_date', 
            'invoice_number', 'amount_total', 'discount_total', 'net_total'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows (one per invoice line item)
        for line_item in data['invoice_line_items']:
            row = {
                'check_info': data['check_info'],
                'vendor_info': data['vendor_info'],
                **line_item
            }
            writer.writerow(row)
        
        print(f"  Exported {len(data['invoice_line_items'])} rows")


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
        if data['invoice_line_items']:  # Only include if we found invoice data
            all_data.append({
                'file_name': pdf_file,
                'data': data
            })
    
    return all_data


def export_all_to_csv(all_data: List[Dict], output_path: str) -> None:
    """Export all remittance data to a single CSV file."""
    print(f"Exporting all data to CSV: {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    total_rows = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'source_file', 'check_info', 'vendor_info', 'invoice_date', 
            'invoice_number', 'amount_total', 'discount_total', 'net_total'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows from all files
        for file_data in all_data:
            file_name = file_data['file_name']
            data = file_data['data']
            
            for line_item in data['invoice_line_items']:
                row = {
                    'source_file': file_name,
                    'check_info': data['check_info'],
                    'vendor_info': data['vendor_info'],
                    **line_item
                }
                writer.writerow(row)
                total_rows += 1
        
        print(f"  Exported {total_rows} total rows from {len(all_data)} files")


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
        invoice_count = len(data['invoice_line_items'])
        total_invoices += invoice_count
        
        print(f"File: {file_name}")
        print(f"  Check Info: {data['check_info']}")
        print(f"  Vendor Info: {data['vendor_info']}")
        print(f"  Invoice Items: {invoice_count}")
        
        for i, item in enumerate(data['invoice_line_items'], 1):
            print(f"    {i}. {item['invoice_date']} | {item['invoice_number']} | ${item['net_total']}")
        print()
    
    print(f"TOTAL: {total_invoices} invoice line items from {len(all_data)} files")
    
    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"remittance_results/remittance_data_{timestamp}.csv"
    export_all_to_csv(all_data, output_file)
    
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Results saved to: {output_file}")


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
            if data['invoice_line_items']:
                all_data = [{'file_name': os.path.basename(args.input), 'data': data}]
                
                # Display extracted data
                print("=== EXTRACTED DATA ===")
                print(f"Check Info: {data['check_info']}")
                print(f"Vendor Info: {data['vendor_info']}")
                print(f"Invoice Items: {len(data['invoice_line_items'])}")
                for i, item in enumerate(data['invoice_line_items'], 1):
                    print(f"  {i}. {item['invoice_date']} | {item['invoice_number']} | ${item['net_total']}")
                
                # Export to CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(args.output, f"remittance_data_{timestamp}.csv")
                export_all_to_csv(all_data, output_file)
                print(f"\nResults saved to: {output_file}")
            else:
                print("No remittance data found in the specified file.")
        else:
            # Process directory
            all_data = process_all_remittance_files(args.input)
            if all_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(args.output, f"remittance_data_{timestamp}.csv")
                export_all_to_csv(all_data, output_file)
                print(f"\nResults saved to: {output_file}")
            else:
                print("No remittance files found to process.")