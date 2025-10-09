#!/usr/bin/env python3
"""
Statement Processing Pipeline

This script processes statement PDFs to extract structured data using pdfplumber
for layout-aware text extraction. It extracts both header information and
invoice line items to generate comprehensive CSV output.

Extracted Fields:
- FILE DATA: file_name
- STATEMENT HEADER DATA: customer_name, account_number, statement_date  
- INVOICE LIST DATA: invoice_date, invoice_number, purchase_order, job_name, charge, credit, balance

Usage:
    python statement_pipeline.py [input_pdf_path]
    python statement_pipeline.py  # Process all PDFs in statement_pdfs folder
"""

import os
import sys
import csv
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import argparse
from pathlib import Path

# Import common utilities
from common_utils import get_pdf_path, setup_output_directory, get_pdf_filename_without_extension

@dataclass
class StatementHeaderData:
    """Container for statement header information."""
    file_name: str
    customer_name: str
    account_number: str
    statement_date: str

@dataclass  
class InvoiceLineItem:
    """Container for individual invoice line item."""
    file_name: str
    customer_name: str
    account_number: str
    statement_date: str
    invoice_date: str
    invoice_number: str
    purchase_order: str
    job_name: str
    charge: str
    credit: str
    balance: str

class StatementProcessor:
    """Main class for processing statement PDFs and extracting structured data."""
    
    def __init__(self, input_pdf_path: str):
        self.input_pdf_path = input_pdf_path
        self.filename = Path(input_pdf_path).name
        self.header_data: Optional[StatementHeaderData] = None
        self.invoice_items: List[InvoiceLineItem] = []
        
    def extract_text_with_pdfplumber(self) -> List[Tuple[int, str]]:
        """
        Extract text from PDF using pdfplumber for structured text layout.
        
        Returns:
            List of (page_number, text_content) tuples
        """
        pages_text = []
        
        print(f"Opening PDF: {self.input_pdf_path}")
        with pdfplumber.open(self.input_pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Processing {total_pages} pages...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        pages_text.append((page_num, text))
                        print(f"Page {page_num}: Extracted {len(text)} characters")
                    else:
                        print(f"Page {page_num}: No text extracted")
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
        
        return pages_text
    
    def extract_header_data(self, text: str) -> Optional[StatementHeaderData]:
        """
        Extract statement header data: customer_name, account_number, statement_date.
        
        Args:
            text: Full page text content
            
        Returns:
            StatementHeaderData object or None if extraction fails
        """
        lines = text.split('\n')
        
        # Initialize data
        customer_name = ""
        account_number = ""
        statement_date = ""
        
        try:
            # Statement date extraction - look for MM/DD/YYYY format in first 10 lines
            for i, line in enumerate(lines[:10]):
                date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', line)
                if date_match and not statement_date:
                    statement_date = date_match.group(1)
                    break
            
            # Account number extraction - look for patterns like "00-0000705"
            for i, line in enumerate(lines):
                account_match = re.search(r'\b((?:00|10|20|22|07)-\d{7})\b', line)
                if account_match:
                    account_number = account_match.group(1)
                    
                    # Customer name is typically 2-3 lines before account number
                    # Look backwards for the customer company name
                    for j in range(max(0, i-5), i):
                        candidate_line = lines[j].strip()
                        # Skip common header elements and look for company names
                        if (candidate_line and 
                            not re.search(r'\d{1,2}/\d{1,2}/\d{4}', candidate_line) and
                            not candidate_line.startswith('P.O. Box') and
                            not candidate_line.startswith('Manhattan') and
                            not candidate_line.startswith('StatementDate') and
                            not candidate_line.startswith('Account') and
                            len(candidate_line) > 5 and
                            not candidate_line.startswith('Page')):
                            # Look for company indicators
                            if any(indicator in candidate_line.upper() for indicator in ['LLC', 'INC', 'CORP', 'GLASS', 'DEPOT', 'SYSTEMS']):
                                customer_name = candidate_line
                                break
                    break
            
            # Fallback customer name extraction if not found above
            if not customer_name:
                # Look for lines between header and account number that contain company-like text
                for i, line in enumerate(lines[5:15], 5):  # Check lines 5-15
                    if (line.strip() and 
                        not re.search(r'\d{1,2}/\d{1,2}/\d{4}', line) and
                        not line.startswith('P.O. Box') and
                        not line.startswith('Manhattan') and
                        len(line.strip()) > 10 and
                        ',' in line):  # Company names often have commas
                        customer_name = line.strip()
                        break
            
            print(f"Extracted header - Customer: '{customer_name}', Account: '{account_number}', Date: '{statement_date}'")
            
            return StatementHeaderData(
                file_name=self.filename,
                customer_name=customer_name,
                account_number=account_number,
                statement_date=statement_date
            )
            
        except Exception as e:
            print(f"Error extracting header data: {e}")
            return None
    
    def extract_invoice_items(self, text: str, header_data: StatementHeaderData) -> List[InvoiceLineItem]:
        """
        Extract invoice line items from the statement.
        
        Args:
            text: Full page text content
            header_data: Previously extracted header information
            
        Returns:
            List of InvoiceLineItem objects
        """
        invoice_items = []
        lines = text.split('\n')
        
        # Find the header row to start parsing from
        header_found = False
        for i, line in enumerate(lines):
            # Look for the invoice header line
            if re.search(r'Date\s+Invoice#.*Charge.*Balance', line, re.IGNORECASE):
                header_found = True
                start_index = i + 1
                print(f"Found invoice header at line {i+1}: {line}")
                break
        
        if not header_found:
            print("Invoice header not found")
            return invoice_items
        
        # Parse invoice lines
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Stop at summary sections
            if any(stop_word in line.upper() for stop_word in ['TOTAL:', 'CURRENT', 'REMIT PAYMENT']):
                print(f"Stopping at summary line: {line}")
                break
            
            # Parse invoice line - expected format:
            # DATE INVOICE# PURCHASE_ORDER JOB_NAME CHARGE [CREDIT] BALANCE
            invoice_item = self.parse_invoice_line(line, header_data)
            if invoice_item:
                invoice_items.append(invoice_item)
                print(f"Parsed invoice: {invoice_item.invoice_number} - {invoice_item.charge}")
        
        print(f"Extracted {len(invoice_items)} invoice items")
        return invoice_items
    
    def parse_invoice_line(self, line: str, header_data: StatementHeaderData) -> Optional[InvoiceLineItem]:
        """
        Parse a single invoice line into structured data.
        
        Expected format variations:
        - 7/22/2025 M708796-IN 13341 THE BALKAN 548.31 548.31
        - 8/28/2025 M708476-IN Labette Bank Labette Bank Doors 6,051.84 6,051.84
        - 7/31/2025 M711015-IN 13367 110.89 110.89 (missing job name)
        - 8/28/2025 M715393-CM 2338559 Pcc Display 127.48 127.48- (CM credit memo with negative balance)
        - 8/14/2025 713936A-PP Ref: ACH081425 96.11 96.11- (PP prepaid with negative balance)
        """
        try:
            # Enhanced regex to extract key components
            # Start with date, then invoice number (flexible patterns), then middle section, then amounts (including negatives)
            # Updated to handle: M/D/W prefixes, numeric prefixes (713936A), -IN/-CM/-PP suffixes, negative amounts
            pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?)\s+(.*?)\s+([\d,]+\.?\d*)(-?)\s+([\d,]+\.?\d*)(-?)$'
            match = re.match(pattern, line)
            
            if not match:
                # Try alternative pattern with credit column (charge, credit, balance)
                pattern_with_credit = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?)\s+(.*?)\s+([\d,]+\.?\d*)(-?)\s+([\d,]+\.?\d*)(-?)\s+([\d,]+\.?\d*)(-?)$'
                match = re.match(pattern_with_credit, line)
                
                if match:
                    invoice_date = match.group(1)
                    invoice_number = match.group(2)
                    middle_section = match.group(3).strip()
                    charge = match.group(4) + match.group(5)  # Combine amount and negative sign
                    credit = match.group(6) + match.group(7)  # Combine amount and negative sign
                    balance = match.group(8) + match.group(9)  # Combine amount and negative sign
                    
                    # Special handling for credit transactions (PP and CM suffixes) in 3-column format
                    # These are credit transactions, but the amounts might be misaligned
                    if invoice_number.endswith('-PP') or invoice_number.endswith('-CM'):
                        # For PP/CM transactions, if we have 3 amounts but it's really CREDIT BALANCE format
                        # The "charge" is actually empty, "credit" is the credit amount, "balance" is balance
                        # But our regex might have captured wrong - let's adjust
                        pass  # The 3-column format should be handled correctly already
                    
                else:
                    return None
            else:
                invoice_date = match.group(1)
                invoice_number = match.group(2)
                middle_section = match.group(3).strip()
                charge = match.group(4) + match.group(5)  # Combine amount and negative sign
                credit = ""  # No credit column in this format
                balance = match.group(6) + match.group(7)  # Combine amount and negative sign
            
            # Special handling for credit transactions (PP and CM suffixes)
            # These are credit transactions where the first amount should be in the credit column
            if invoice_number.endswith('-PP') or invoice_number.endswith('-CM'):
                # For PP/CM transactions: DATE INVOICE MIDDLE CREDIT BALANCE
                # Move charge to credit column and clear charge
                credit = charge
                charge = ""
            
            # Parse middle section for purchase_order and job_name
            # This is the tricky part as the format varies
            purchase_order, job_name = self.parse_middle_section(middle_section)
            
            return InvoiceLineItem(
                file_name=header_data.file_name,
                customer_name=header_data.customer_name,
                account_number=header_data.account_number,
                statement_date=header_data.statement_date,
                invoice_date=invoice_date,
                invoice_number=invoice_number,
                purchase_order=purchase_order,
                job_name=job_name,
                charge=charge,
                credit=credit,
                balance=balance
            )
            
        except Exception as e:
            print(f"Error parsing invoice line '{line}': {e}")
            return None
    
    def extract_with_positional_parsing(self, input_pdf_path: str) -> List[InvoiceLineItem]:
        """
        Extract invoice items using positional/columnar parsing with pdfplumber coordinates.
        This approach uses the actual column positions to determine Purchase Order vs Job Name.
        
        Returns:
            List of InvoiceLineItem objects
        """
        invoice_items = []
        
        try:
            with pdfplumber.open(input_pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract words with position information
                    words = page.extract_words(extra_attrs=["x0", "x1", "top", "bottom"])
                    
                    if not words:
                        continue
                    
                    # Group words by lines (similar top position)
                    lines_dict = self.group_words_by_lines(words)
                    
                    # Find header line to establish column boundaries
                    column_boundaries = self.find_column_boundaries(lines_dict)
                    
                    if not column_boundaries:
                        print(f"Page {page_num}: Could not establish column boundaries, falling back to text parsing")
                        continue
                    
                    # Extract header data if this is the first page
                    if page_num == 1 and not self.header_data:
                        page_text = page.extract_text()
                        self.header_data = self.extract_header_data(page_text)
                    
                    # Skip if header_data is not available
                    if not self.header_data:
                        print(f"Page {page_num}: Header data not available, skipping")
                        continue
                    
                    # Process invoice lines using positional data
                    page_items = self.parse_invoice_lines_positional(lines_dict, column_boundaries, self.header_data)
                    invoice_items.extend(page_items)
                    
                    print(f"Page {page_num}: Extracted {len(page_items)} items using positional parsing")
        
        except Exception as e:
            print(f"Error in positional parsing: {e}")
            
        return invoice_items
    
    def group_words_by_lines(self, words: List[Dict]) -> Dict[float, List[Dict]]:
        """Group words by their vertical position (lines)."""
        lines_dict = {}
        tolerance = 3  # pixels
        
        for word in words:
            # Round to nearest tolerance to group words on same line
            y_key = round(word['top'] / tolerance) * tolerance
            if y_key not in lines_dict:
                lines_dict[y_key] = []
            lines_dict[y_key].append(word)
        
        # Sort words within each line by x position
        for y_pos in lines_dict:
            lines_dict[y_pos].sort(key=lambda w: w['x0'])
            
        return lines_dict
    
    def find_column_boundaries(self, lines_dict: Dict[float, List[Dict]]) -> Optional[Dict[str, float]]:
        """Find column boundaries from the header line."""
        for y_pos, line_words in lines_dict.items():
            line_text = " ".join([w['text'] for w in line_words])
            
            # Look for the header line with more flexible matching
            if ('Date' in line_text and 'Invoice' in line_text and 
                ('Purchase' in line_text or 'PO' in line_text) and
                ('Job' in line_text or 'Name' in line_text) and 
                ('Charge' in line_text or 'Amount' in line_text)):
                
                po_start = None
                job_start = None
                charge_start = None
                
                for word in line_words:
                    word_text = word['text']
                    # More flexible purchase order detection
                    if 'Purchase' in word_text or (word_text == 'PO'):
                        po_start = word['x0']
                    # Use 'Job' word position, not 'Name' - this is the key fix!
                    elif word_text == 'Job':
                        job_start = word['x0']
                    # More flexible charge detection
                    elif 'Charge' in word_text or 'Amount' in word_text:
                        charge_start = word['x0']
                
                if po_start and job_start and charge_start:
                    print(f"Found column boundaries - PO: {po_start}, Job: {job_start}, Charge: {charge_start}")
                    return {
                        'purchase_order_start': po_start,
                        'job_name_start': job_start,
                        'charge_start': charge_start
                    }
                else:
                    print(f"Header found but missing boundaries: PO={po_start}, Job={job_start}, Charge={charge_start}")
        
        print("No suitable header line found for column boundaries")
        return None
    
    def parse_invoice_lines_positional(self, lines_dict: Dict[float, List[Dict]], 
                                     column_boundaries: Dict[str, float], 
                                     header_data: StatementHeaderData) -> List[InvoiceLineItem]:
        """Parse invoice lines using positional column data."""
        invoice_items = []
        
        po_start = column_boundaries['purchase_order_start']
        job_start = column_boundaries['job_name_start']
        charge_start = column_boundaries['charge_start']
        
        for y_pos, line_words in lines_dict.items():
            line_text = " ".join([w['text'] for w in line_words])
            
            # Check if this is an invoice line (contains date and invoice number patterns)
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', line_text) and re.search(r'[MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?', line_text):
                # Skip summary lines
                if any(stop_word in line_text.upper() for stop_word in ['TOTAL:', 'CURRENT', 'REMIT PAYMENT']):
                    continue
                
                try:
                    # Extract basic data (date, invoice, amounts) using regex
                    invoice_item = self.parse_basic_invoice_data(line_text, header_data)
                    
                    if invoice_item:
                        # Override purchase_order and job_name with positional data
                        po_words = [w for w in line_words if po_start <= w['x0'] < job_start]
                        job_words = [w for w in line_words if job_start <= w['x0'] < charge_start]
                        
                        # Handle PP transactions specially - they have no purchase order
                        if invoice_item.invoice_number.endswith('-PP'):
                            invoice_item.purchase_order = ""
                            invoice_item.job_name = " ".join([w['text'] for w in job_words])
                        else:
                            invoice_item.purchase_order = " ".join([w['text'] for w in po_words])
                            invoice_item.job_name = " ".join([w['text'] for w in job_words])
                        
                        invoice_items.append(invoice_item)
                        print(f"Positional parse: {invoice_item.invoice_number} -> PO:'{invoice_item.purchase_order}' Job:'{invoice_item.job_name}'")
                
                except Exception as e:
                    print(f"Error parsing line positionally: {line_text}: {e}")
        
        return invoice_items
    
    def parse_basic_invoice_data(self, line: str, header_data: StatementHeaderData) -> Optional[InvoiceLineItem]:
        """Parse basic invoice data (date, invoice#, amounts) without middle section."""
        try:
            # Use existing regex patterns to extract date, invoice, and amounts
            pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?)\s+(.*?)\s+([\d,]+\.?\d*)(-?)\s+([\d,]+\.?\d*)(-?)$'
            match = re.match(pattern, line)
            
            if not match:
                return None
            
            invoice_date = match.group(1)
            invoice_number = match.group(2)
            charge = match.group(4) + match.group(5)
            credit = ""
            balance = match.group(6) + match.group(7)
            
            # Handle credit transactions (PP and CM)
            if invoice_number.endswith('-PP') or invoice_number.endswith('-CM'):
                credit = charge
                charge = ""
            
            return InvoiceLineItem(
                file_name=header_data.file_name,
                customer_name=header_data.customer_name,
                account_number=header_data.account_number,
                statement_date=header_data.statement_date,
                invoice_date=invoice_date,
                invoice_number=invoice_number,
                purchase_order="",  # Will be set by positional parsing
                job_name="",       # Will be set by positional parsing
                charge=charge,
                credit=credit,
                balance=balance
            )
            
        except Exception as e:
            print(f"Error in basic parsing: {e}")
            return None
    
    def parse_middle_section(self, middle_section: str) -> Tuple[str, str]:
        """
        Parse the middle section between invoice number and charge to extract
        purchase_order and job_name.
        
        Examples:
        - "13341 THE BALKAN" -> purchase_order="13341", job_name="THE BALKAN"
        - "Labette Bank Labette Bank Doors" -> purchase_order="", job_name="Labette Bank Labette Bank Doors"
        - "13367" -> purchase_order="13367", job_name=""
        - "STOCK LAMI S/S" -> purchase_order="", job_name="STOCK LAMI S/S"
        """
        parts = middle_section.split()
        
        if not parts:
            return "", ""
        
        # Check if first part looks like a purchase order (numeric)
        if parts[0].isdigit():
            purchase_order = parts[0]
            job_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        else:
            # No clear purchase order, treat everything as job name
            purchase_order = ""
            job_name = middle_section
        
        return purchase_order, job_name
    
    def generate_csv_output(self, output_dir: str) -> str:
        """
        Generate CSV file with all extracted statement data.
        
        Args:
            output_dir: Directory to save the CSV file
            
        Returns:
            Path to the generated CSV file
        """
        if not self.invoice_items:
            print("No invoice items to export")
            return ""
        
        # Create output filename
        base_name = get_pdf_filename_without_extension(self.input_pdf_path)
        csv_filename = f"{base_name}_statement_data.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        # CSV headers
        headers = [
            'file_name', 'customer_name', 'account_number', 'statement_date',
            'invoice_date', 'invoice_number', 'purchase_order', 'job_name',
            'charge', 'credit', 'balance'
        ]
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                for item in self.invoice_items:
                    writer.writerow([
                        item.file_name,
                        item.customer_name,
                        item.account_number,
                        item.statement_date,
                        item.invoice_date,
                        item.invoice_number,
                        item.purchase_order,
                        item.job_name,
                        item.charge,
                        item.credit,
                        item.balance
                    ])
            
            print(f"CSV exported: {csv_path}")
            print(f"Exported {len(self.invoice_items)} invoice items")
            return csv_path
            
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return ""
    
    def process_statement(self) -> bool:
        """
        Main processing method that orchestrates the entire pipeline.
        
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {self.filename}")
            print(f"{'='*60}")
            
            # Try positional parsing first (more accurate for columnar data)
            print("Attempting positional parsing...")
            positional_items = self.extract_with_positional_parsing(self.input_pdf_path)
            
            if positional_items:
                print(f"✅ Positional parsing successful: {len(positional_items)} items extracted")
                self.invoice_items = positional_items
            else:
                print("⚠️ Positional parsing failed, falling back to text-based parsing...")
                
                # Fallback to original text-based approach
                # Step 1: Extract text using pdfplumber
                pages_text = self.extract_text_with_pdfplumber()
                if not pages_text:
                    print("No text extracted from PDF")
                    return False
                
                # Step 2: Extract header data from first page
                first_page_text = pages_text[0][1]
                self.header_data = self.extract_header_data(first_page_text)
                
                if not self.header_data:
                    print("Failed to extract header data")
                    return False
                
                # Step 3: Extract invoice items from all pages using text parsing
                for page_num, text in pages_text:
                    page_items = self.extract_invoice_items(text, self.header_data)
                    self.invoice_items.extend(page_items)
            
            # Step 4: Generate CSV output
            output_dir = setup_output_directory("statement_results")
            csv_path = self.generate_csv_output(output_dir)
            
            if csv_path:
                print(f"\n✅ Processing completed successfully!")
                print(f"📄 Header data extracted: {self.header_data.customer_name if self.header_data else 'N/A'}")
                print(f"📋 Invoice items extracted: {len(self.invoice_items)}")
                print(f"💾 CSV saved: {csv_path}")
                return True
            else:
                print("❌ Failed to generate CSV output")
                return False
                
        except Exception as e:
            print(f"❌ Error processing statement: {e}")
            return False

def process_single_statement(pdf_path: str) -> bool:
    """Process a single statement PDF file."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    processor = StatementProcessor(pdf_path)
    return processor.process_statement()

def process_all_statements(statements_dir: str) -> None:
    """Process all PDF files in the statements directory."""
    if not os.path.exists(statements_dir):
        print(f"Error: Directory not found: {statements_dir}")
        return
    
    pdf_files = [f for f in os.listdir(statements_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in: {statements_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(statements_dir, pdf_file)
        if process_single_statement(pdf_path):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total files: {len(pdf_files)}")

def main():
    """Main entry point for the statement processing pipeline."""
    parser = argparse.ArgumentParser(description='Process statement PDFs and extract structured data')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file to process')
    parser.add_argument('--dir', help='Directory containing statement PDFs to process')
    
    args = parser.parse_args()
    
    if args.pdf_path:
        # Process single file
        process_single_statement(args.pdf_path)
    elif args.dir:
        # Process directory
        process_all_statements(args.dir)
    else:
        # Default: process statement_pdfs directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        statements_dir = os.path.join(script_dir, 'statement_pdfs')
        process_all_statements(statements_dir)

if __name__ == "__main__":
    main()