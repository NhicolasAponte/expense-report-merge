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
    
    def is_new_customer_page(self, text: str) -> bool:
        """
        Check if this page starts a new customer statement by looking for multiple indicators:
        1. Location headers (Manko Window Systems - [Location] or Interstate Glass)
        2. Page 1 indicator 
        3. Statement Date presence
        4. Account # presence
        
        Args:
            text: Page text content
            
        Returns:
            True if this is a new customer page, False otherwise
        """
        # Check for location headers
        has_location_header = any([
            "Manko Window Systems - Manhattan Location" in text,
            "Manko Window Systems - Aurora Location" in text, 
            "Manko Window Systems - Des Moines Location" in text,
            "Interstate Glass" in text
        ])
        
        # Check for Page 1 (indicating start of customer statement)
        import re
        has_page_one = bool(re.search(r'Page\s+1\b', text))
        
        # Check for required elements
        has_statement_date = "StatementDate" in text or "Statement Date" in text
        has_account = "Account #" in text
        
        # A new customer page should have all these elements
        return has_location_header and has_page_one and has_statement_date and has_account
    
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
                    
                    # Customer name is typically 1-2 lines before account number line
                    # Look backwards for the customer company name
                    for j in range(max(0, i-3), i):
                        candidate_line = lines[j].strip()
                        # Skip common header elements and look for company names
                        if (candidate_line and 
                            not re.search(r'\d{1,2}/\d{1,2}/\d{4}', candidate_line) and
                            not candidate_line.startswith('P.O. Box') and
                            not candidate_line.startswith('Manhattan') and
                            not candidate_line.startswith('StatementDate') and
                            not candidate_line.startswith('Account') and
                            len(candidate_line) > 5 and
                            not candidate_line.startswith('Page') and
                            # Exclude address patterns (city, state zip)
                            not re.search(r'^[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}', candidate_line) and
                            # Exclude lines that are mostly street addresses 
                            not re.search(r'^\d+\s+[A-Za-z\s]+(Dr|St|Ave|Blvd|Rd|Court|Way|Plaza)', candidate_line, re.IGNORECASE)):
                            
                            # First priority: Lines with strong company indicators
                            if any(indicator in candidate_line.upper() for indicator in ['LLC', 'INC', 'CORP', 'GLASS', 'DEPOT', 'SYSTEMS', 'COMPANY', 'CO.', 'LTD']):
                                customer_name = candidate_line
                                break
                            # Second priority: Lines that look like company names (capital letters, multiple words)
                            elif (len(candidate_line.split()) >= 2 and
                                  not candidate_line.islower() and
                                  not re.search(r'^\d+', candidate_line) and  # Doesn't start with number (address)
                                  # Not a typical address pattern
                                  not re.search(r'\d{5}', candidate_line)):  # No zip code
                                if not customer_name:  # Only if we haven't found a better match
                                    customer_name = candidate_line
                    break
            
            # Fallback customer name extraction if not found above
            if not customer_name:
                # Look for the line immediately after "Account #" - this is usually the customer name
                for i, line in enumerate(lines):
                    if line.strip() == "Account #" and i + 1 < len(lines):
                        candidate = lines[i + 1].strip()
                        # Make sure it's not an address line
                        if (candidate and 
                            len(candidate) > 5 and
                            not re.search(r'^[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}', candidate) and
                            not re.search(r'^\d+\s+[A-Za-z\s]+(Dr|St|Ave|Blvd|Rd|Court|Way|Plaza)', candidate, re.IGNORECASE)):
                            customer_name = candidate
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
        Extract invoice items using positional/columnar parsing with layout-aware text extraction.
        This approach uses pdfplumber's layout=True to preserve column positioning.
        
        Returns:
            List of InvoiceLineItem objects
        """
        invoice_items = []
        
        try:
            with pdfplumber.open(input_pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Use layout-aware text extraction to preserve column structure
                    page_text = page.extract_text(layout=True)
                    
                    if not page_text:
                        continue
                    
                    # Check if this is a new customer page
                    standard_text = page.extract_text()  # Get standard text for header parsing
                    
                    if self.is_new_customer_page(standard_text):
                        # Extract header data for this new customer
                        new_header_data = self.extract_header_data(standard_text)
                        if new_header_data:
                            self.header_data = new_header_data
                            print(f"Page {page_num}: New customer detected - {self.header_data.customer_name} | {self.header_data.account_number}")
                        else:
                            print(f"Page {page_num}: Failed to extract header data for new customer page")
                    
                    # Skip if header_data is not available
                    if not self.header_data:
                        print(f"Page {page_num}: Header data not available, skipping")
                        continue
                    
                    # Find column boundaries and process invoice lines using layout-aware text
                    column_boundaries = self.find_column_boundaries_from_layout(page_text)
                    
                    if not column_boundaries:
                        print(f"Page {page_num}: Could not establish column boundaries from layout, falling back to text parsing")
                        continue
                    
                    # Process invoice lines using positional data from layout-aware text
                    page_items = self.parse_invoice_lines_from_layout(page_text, column_boundaries, self.header_data)
                    invoice_items.extend(page_items)
                    
                    print(f"Page {page_num}: Extracted {len(page_items)} items using layout-aware positional parsing")
        
        except Exception as e:
            print(f"Error in positional parsing: {e}")
            
        return invoice_items
    
    def find_column_boundaries_from_layout(self, layout_text: str) -> Optional[Dict[str, int]]:
        """
        Find column boundaries from layout-aware text extraction.
        This uses the preserved spacing to determine column positions.
        
        Args:
            layout_text: Text extracted with layout=True
            
        Returns:
            Dictionary with column start positions or None if not found
        """
        lines = layout_text.split('\n')
        
        for line in lines:
            # Look for the header line
            if ('Date' in line and 'Invoice' in line and 
                'PurchaseOrder' in line and 'JobName' in line and 
                'Charge' in line):
                
                # Find the position of each column header
                po_start = line.find('PurchaseOrder')
                job_start = line.find('JobName')
                charge_start = line.find('Charge')
                
                if po_start >= 0 and job_start >= 0 and charge_start >= 0:
                    print(f"Found layout column boundaries - PO: {po_start}, Job: {job_start}, Charge: {charge_start}")
                    return {
                        'purchase_order_start': po_start,
                        'job_name_start': job_start,
                        'charge_start': charge_start
                    }
        
        print("No suitable header line found for layout column boundaries")
        return None
    
    def parse_invoice_lines_from_layout(self, layout_text: str, 
                                       column_boundaries: Dict[str, int], 
                                       header_data: StatementHeaderData) -> List[InvoiceLineItem]:
        """
        Parse invoice lines using layout-aware text with intelligent field boundary detection.
        
        Args:
            layout_text: Text extracted with layout=True
            column_boundaries: Dictionary with column start positions
            header_data: Previously extracted header information
            
        Returns:
            List of InvoiceLineItem objects
        """
        invoice_items = []
        lines = layout_text.split('\n')
        
        po_start = column_boundaries['purchase_order_start']
        job_start = column_boundaries['job_name_start']
        charge_start = column_boundaries['charge_start']
        
        for line in lines:
            # Check if this is an invoice line (contains date and invoice number patterns)
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', line) and re.search(r'[MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?', line):
                # Skip summary lines
                if any(stop_word in line.upper() for stop_word in ['TOTAL:', 'CURRENT', 'REMIT PAYMENT']):
                    continue
                
                try:
                    # Extract basic data (date, invoice, amounts) using regex on the line
                    invoice_item = self.parse_basic_invoice_data(line.strip(), header_data)
                    
                    if invoice_item:
                        # Extract the text section that contains PO and Job names
                        text_section = line[po_start:charge_start].strip() if len(line) > po_start else ""
                        
                        if invoice_item.invoice_number.endswith('-PP'):
                            # PP transactions have no purchase order, everything goes to job name
                            invoice_item.purchase_order = ""
                            # Clean and assign to job name
                            job_text = re.sub(r'\d+\.\d+', '', text_section).strip()
                            invoice_item.job_name = job_text
                        else:
                            # Normal transactions: intelligently split between PO and Job fields
                            po_text, job_text = self.smart_split_po_job_fields(text_section, line, po_start, job_start, charge_start)
                            
                            invoice_item.purchase_order = po_text
                            invoice_item.job_name = job_text
                        
                        invoice_items.append(invoice_item)
                        print(f"Layout parse: {invoice_item.invoice_number} -> PO:'{invoice_item.purchase_order}' Job:'{invoice_item.job_name}'")
                
                except Exception as e:
                    print(f"Error parsing line with layout: {line.strip()}: {e}")
        
        return invoice_items
    
    def smart_split_po_job_fields(self, text_section: str, full_line: str, po_start: int, job_start: int, charge_start: int) -> Tuple[str, str]:
        """
        Intelligently split the text section between Purchase Order and Job Name fields.
        Uses multiple strategies to determine the optimal split point.
        
        Args:
            text_section: The text content between PO start and Charge start
            full_line: The complete line for position analysis
            po_start: Purchase Order column start position
            job_start: Job Name column start position  
            charge_start: Charge column start position
            
        Returns:
            Tuple of (purchase_order_text, job_name_text)
        """
        # Clean numeric contamination first
        clean_text = re.sub(r'\d+\.\d+', '', text_section).strip()
        
        if not clean_text:
            return "", ""
        
        # Strategy 1: Look for natural word boundaries around the job_start position
        relative_job_start = job_start - po_start
        
        # Check if there's a clear word break near the job_start boundary
        words = clean_text.split()
        
        if len(words) <= 1:
            # Single word or empty - determine which field it belongs to
            if len(clean_text) <= 14:  # Short names likely go to PO
                return clean_text, ""
            else:  # Long names might be job names
                return "", clean_text
        
        # Strategy 2: For multi-word content, find the best split point
        if len(words) == 2:
            # Two words: check positioning and common patterns
            word1, word2 = words
            
            # Special case: "STOCK SHEETS", "STOCK LAMI" should be PO
            if word1 == "STOCK":
                return clean_text, ""
            
            # For names like "ERNEST HALF", check positions in the original line
            word1_pos = full_line.find(word1, po_start)
            word2_pos = full_line.find(word2, po_start)
            
            if word1_pos >= 0 and word2_pos >= 0:
                # If second word starts near or after job_start, split there
                if word2_pos >= job_start - 2:  # Small tolerance
                    return word1, word2
                # If both words are well before job_start, keep together as PO
                elif word2_pos < job_start - 4:
                    return clean_text, ""
            
            # Default: first word to PO, second to Job
            return word1, word2
        
        elif len(words) == 3:
            # Three words: likely "FIRST SECOND THIRD" -> PO="FIRST", Job="SECOND THIRD"
            return words[0], " ".join(words[1:])
        
        elif len(words) >= 4:
            # Many words: split roughly in the middle, favoring Job field for longer content
            mid_point = len(words) // 2
            return " ".join(words[:mid_point]), " ".join(words[mid_point:])
        
        # Fallback: use the original boundary-based approach
        po_section = full_line[po_start:job_start].strip() if len(full_line) > po_start else ""
        job_section = full_line[job_start:charge_start].strip() if len(full_line) > job_start else ""
        
        po_clean = re.sub(r'\d+\.\d+', '', po_section).strip()
        job_clean = re.sub(r'\d+\.\d+', '', job_section).strip()
        
        return po_clean, job_clean
    
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
        """Find column boundaries from the header line using exact word matches."""
        for y_pos, line_words in lines_dict.items():
            line_text = " ".join([w['text'] for w in line_words])
            
            # Look for the header line with exact matches
            if ('Date' in line_text and 'Invoice' in line_text and 
                'PurchaseOrder' in line_text and 'JobName' in line_text and 
                'Charge' in line_text):
                
                po_start = None
                job_start = None
                charge_start = None
                
                for word in line_words:
                    word_text = word['text']
                    # Exact word matching for more precision
                    if word_text == 'PurchaseOrder':
                        po_start = word['x0']
                    elif word_text == 'JobName':
                        job_start = word['x0']
                    elif word_text == 'Charge':
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
                        # Assign words to columns based on position, with special logic for field boundaries
                        po_words = []
                        job_words = []
                        
                        for word in line_words:
                            word_x = word['x0']
                            word_text = word['text']
                            
                            # Skip date, invoice number, and numeric fields
                            if (re.match(r'\d{1,2}/\d{1,2}/\d{4}', word_text) or  # Date
                                re.match(r'[MDW]?\d+[A-Z]*(?:-(?:IN|CM|PP))?', word_text) or  # Invoice number
                                re.match(r'\d+\.?\d*', word_text)):  # Numeric amounts
                                continue
                            
                            # For PP transactions, everything between invoice and charge goes to Job Name
                            if invoice_item.invoice_number.endswith('-PP'):
                                if job_start <= word_x < charge_start:
                                    job_words.append(word_text)
                            else:
                                # Normal assignment logic with smart boundary handling
                                if po_start <= word_x < job_start:
                                    po_words.append(word_text)
                                elif job_start <= word_x < charge_start:
                                    job_words.append(word_text)
                                # Special case: if a word is very close to job_start boundary (within 5 points)
                                # and we already have PO words, assign it to Job Name
                                elif (job_start - 5) <= word_x < job_start and po_words:
                                    job_words.append(word_text)
                        
                        # Handle PP transactions specially - they have no purchase order
                        if invoice_item.invoice_number.endswith('-PP'):
                            invoice_item.purchase_order = ""
                            invoice_item.job_name = " ".join(job_words)
                        else:
                            invoice_item.purchase_order = " ".join(po_words)
                            invoice_item.job_name = " ".join(job_words)
                        
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
    
    def generate_csv_output(self, output_dir: str) -> Dict[str, str]:
        """
        Generate separate CSV files based on invoice number suffixes.
        - statement_data.csv: Regular invoices (no special suffix)
        - cm_statement.csv: Credit memo transactions (-CM)
        - pp_statement.csv: Payment transactions (-PP)
        
        Args:
            output_dir: Directory to save the CSV files
            
        Returns:
            Dictionary with paths to generated CSV files
        """
        if not self.invoice_items:
            print("No invoice items to export")
            return {}
        
        # Separate items by invoice number suffix
        regular_items = []  # Default invoices (no special suffix)
        cm_items = []       # Credit memo transactions (-CM)
        pp_items = []       # Payment transactions (-PP)
        
        for item in self.invoice_items:
            if item.invoice_number.endswith('-CM'):
                cm_items.append(item)
            elif item.invoice_number.endswith('-PP'):
                pp_items.append(item)
            else:
                regular_items.append(item)
        
        generated_files = {}
        
        # Generate statement_data.csv for regular invoices
        if regular_items:
            regular_csv_path = os.path.join(output_dir, "statement_data.csv")
            self._write_csv_file(regular_csv_path, regular_items)
            generated_files['statement_data'] = regular_csv_path
            print(f"Generated statement_data.csv: {len(regular_items)} regular invoice items")
        
        # Generate cm_statement.csv for credit memo transactions
        if cm_items:
            cm_csv_path = os.path.join(output_dir, "cm_statement.csv")
            self._write_csv_file(cm_csv_path, cm_items)
            generated_files['cm_statement'] = cm_csv_path
            print(f"Generated cm_statement.csv: {len(cm_items)} credit memo items")
        
        # Generate pp_statement.csv for payment transactions
        if pp_items:
            pp_csv_path = os.path.join(output_dir, "pp_statement.csv")
            self._write_csv_file(pp_csv_path, pp_items)
            generated_files['pp_statement'] = pp_csv_path
            print(f"Generated pp_statement.csv: {len(pp_items)} payment items")
        
        return generated_files
    
    def _write_csv_file(self, csv_path: str, items: List[InvoiceLineItem]) -> None:
        """
        Write invoice items to a CSV file.
        
        Args:
            csv_path: Path to the CSV file to create
            items: List of InvoiceLineItem objects to write
        """
        headers = [
            'file_name', 'customer_name', 'account_number', 'statement_date',
            'invoice_date', 'invoice_number', 'purchase_order', 'job_name',
            'charge', 'credit', 'balance'
        ]
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                for item in items:
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
            
        except Exception as e:
            print(f"Error generating CSV: {e}")
    
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
                print(f"[SUCCESS] Positional parsing successful: {len(positional_items)} items extracted")
                self.invoice_items = positional_items
            else:
                print("[WARNING] Positional parsing failed, falling back to text-based parsing...")
                
                # Fallback to original text-based approach
                # Step 1: Extract text using pdfplumber
                pages_text = self.extract_text_with_pdfplumber()
                if not pages_text:
                    print("No text extracted from PDF")
                    return False
                
                # Step 2: Process each page and extract header data when new customer detected
                for page_num, page_text in pages_text:
                    if self.is_new_customer_page(page_text):
                        # Extract header data for this new customer
                        new_header_data = self.extract_header_data(page_text)
                        if new_header_data:
                            self.header_data = new_header_data
                            print(f"Page {page_num}: New customer detected - {self.header_data.customer_name} | {self.header_data.account_number}")
                    
                    if self.header_data:
                        # Extract invoice items from this page
                        page_items = self.extract_invoice_items(page_text, self.header_data)
                        self.invoice_items.extend(page_items)
                
                if not self.header_data:
                    print("Failed to extract any header data from document")
                    return False
            
            # Step 3: Generate CSV output
            output_dir = setup_output_directory("statement_results")
            generated_files = self.generate_csv_output(output_dir)
            
            if generated_files:
                print(f"\n[SUCCESS] Processing completed successfully!")
                print(f"📄 Header data extracted: {self.header_data.customer_name if self.header_data else 'N/A'}")
                print(f"📋 Invoice items extracted: {len(self.invoice_items)}")
                for file_type, file_path in generated_files.items():
                    print(f"💾 CSV saved ({file_type}): {file_path}")
                return True
            else:
                print("[ERROR] Failed to generate CSV output")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error processing statement: {e}")
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
    print(f"[SUCCESS] Successful: {successful}")
    print(f"[ERROR] Failed: {failed}")
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