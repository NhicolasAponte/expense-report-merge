#!/usr/bin/env python3
"""
Unified Paystub Processing Pipeline

This script serves as the single entry point for the paystub processing system.
It orchestrates the entire pipeline:
1. PDF text extraction using pdfplumber for structured text layout
2. Employee data extraction using centralized regex patterns
3. Section data extraction (earnings, tax deductions, deductions)
4. CSV output generation

Output files:
- earnings.csv: employee_data + earnings_data (with hours)
- tax_deductions.csv: employee_data + tax_deductions_data
- deductions.csv: employee_data + deductions_data

Usage:
    python paystub_pipeline.py [input_pdf_path]
"""

import os
import sys
import csv
import pdfplumber
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import argparse

# Import common utilities
from common_utils import get_pdf_path, setup_output_directory, get_pdf_filename_without_extension

# Import our centralized regex patterns
from regex_patterns.employee_regex import extract_employee_data_patterns
from regex_patterns.earnings_regex import extract_earnings_data
from regex_patterns.deductions_regex import extract_tax_deductions_data, extract_deductions_data


@dataclass
class EmployeeData:
    """Container for employee information extracted from paystub."""
    page_number: int
    employee_name: str
    employee_number: str
    pay_rate: str
    stub_number: str
    period_end: str


@dataclass
class EarningsRecord:
    """Container for earnings data with employee context."""
    employee: EmployeeData
    category: str
    hours: float
    amount: float
    ytd: float


@dataclass
class DeductionRecord:
    """Container for deduction data with employee context."""
    employee: EmployeeData
    category: str
    amount: float
    ytd: float


class PaystubPipeline:
    """Main pipeline orchestrator for paystub processing."""
    
    def __init__(self, input_pdf_path: str, output_dir: Optional[str] = None):
        """
        Initialize the pipeline.
        
        Args:
            input_pdf_path: Path to the input PDF file
            output_dir: Directory for output files (defaults to result-files/)
        """
        self.input_pdf_path = input_pdf_path
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "result-files")
        self.filename = os.path.basename(input_pdf_path)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Storage for extracted data
        self.earnings_records: List[EarningsRecord] = []
        self.tax_deductions_records: List[DeductionRecord] = []
        self.deductions_records: List[DeductionRecord] = []
    
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
    
    def extract_employee_data(self, page_num: int, text: str) -> Optional[EmployeeData]:
        """
        Extract employee data from page text using patterns adapted for pdfplumber format.
        
        Args:
            page_num: Page number
            text: Page text content from pdfplumber
            
        Returns:
            EmployeeData object or None if extraction fails
        """
        try:
            # pdfplumber extracts data in a more structured format
            # Try centralized patterns first
            employee_data = extract_employee_data_patterns(text, page_num)
            
            # If centralized patterns don't work, use pdfplumber-specific patterns
            if not employee_data.get('employee_name') or not employee_data.get('employee_number'):
                employee_data = self.extract_employee_data_pdfplumber_format(text, page_num)
            
            if not employee_data:
                print(f"Page {page_num}: No employee data found")
                return None
            
            return EmployeeData(
                page_number=page_num,
                employee_name=employee_data.get('employee_name', ''),
                employee_number=employee_data.get('employee_number', ''),
                pay_rate=employee_data.get('pay_rate', ''),
                stub_number=employee_data.get('stub_number', ''),
                period_end=employee_data.get('period_end', '')
            )
            
        except Exception as e:
            print(f"Error extracting employee data from page {page_num}: {e}")
            return None
    
    def extract_employee_data_pdfplumber_format(self, text: str, page_num: int) -> Dict[str, str]:
        """
        Extract employee data using patterns specific to pdfplumber's text format.
        
        Args:
            text: Text extracted by pdfplumber
            page_num: Page number for reference
            
        Returns:
            Dictionary with employee data
        """
        import re
        
        employee_data = {
            'page_number': str(page_num),
            'employee_name': '',
            'employee_number': '',
            'pay_rate': '',
            'stub_number': '',
            'period_end': ''
        }
        
        lines = text.split('\n')
        
        # Pattern 1: Name and date on same line - enhanced to handle name suffixes and OCR errors
        # Examples: "Dakota J. Ausmus 9/19/2025", "JoelT.Scheuerman 9/19/2025", "Lawrence Porter III 9/19/2025"
        name_date_pattern = r'^([A-Za-z][A-Za-z\s\.\'\-,]*[A-Za-z](?:\s+(?:III|Jr\.?|Sr\.?))?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
        
        # Fallback pattern for names with OCR errors (111 instead of III, 0. instead of O., etc.)
        name_date_fallback_pattern = r'^([A-Za-z][A-Za-z\s\.0-9\'\-,]*[A-Za-z0-9](?:\s+(?:111|Jr\.?|Sr\.?))?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
        
        # Pattern 2: Data line like "00-AER ···-**-0489 17.50 HW 9/13/2025 D000122839"
        # Updated to handle various bullet characters in SSN masking and multiple department codes
        data_line_pattern = r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
        
        # Fallback pattern for OCR errors where '00-' or '07-' becomes 'oo-' or 'o7-'
        data_line_fallback_pattern = r'^([o0][o07]-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$'
        
        for line in lines:
            line = line.strip()
            
            # Try to match name and date
            match = re.match(name_date_pattern, line)
            if match and not employee_data['employee_name']:
                candidate_name = match.group(1).strip()
                # Enhanced name validation - allow names with or without spaces (like JoelT.Scheuerman)
                if len(candidate_name) >= 3 and ((' ' in candidate_name) or ('.' in candidate_name and len(candidate_name) >= 8)):
                    employee_data['employee_name'] = candidate_name
                    # Note: This date might be different from period_end
            elif not employee_data['employee_name']:
                # Try fallback pattern for OCR errors in names
                fallback_match = re.match(name_date_fallback_pattern, line)
                if fallback_match:
                    candidate_name = fallback_match.group(1).strip()
                    # Clean up OCR errors: 0. -> O., 111 -> III (when part of name suffix)
                    candidate_name = re.sub(r'\b0\.', 'O.', candidate_name)
                    candidate_name = re.sub(r'\s111$', ' III', candidate_name)
                    # Enhanced name validation
                    if len(candidate_name) >= 3 and ((' ' in candidate_name) or ('.' in candidate_name and len(candidate_name) >= 8)):
                        employee_data['employee_name'] = candidate_name
            
            # Try to match the data line with employee number, pay rate, period end, stub number
            match = re.match(data_line_pattern, line)
            if match:
                employee_data['employee_number'] = match.group(1)
                employee_data['pay_rate'] = match.group(2)
                employee_data['period_end'] = match.group(3)
                employee_data['stub_number'] = match.group(4)
            elif not employee_data['employee_number']:
                # Try fallback pattern for OCR errors (oo-/o7- instead of 00-/07-)
                fallback_match = re.match(data_line_fallback_pattern, line, re.IGNORECASE)
                if fallback_match:
                    # Correct the OCR error: replace oo-/o7- with 00-/07-
                    emp_num = fallback_match.group(1)
                    emp_num_corrected = re.sub(r'^o([o07])-', r'0\1-', emp_num, flags=re.IGNORECASE)
                    employee_data['employee_number'] = emp_num_corrected
                    employee_data['pay_rate'] = fallback_match.group(2)
                    employee_data['period_end'] = fallback_match.group(3)
                    employee_data['stub_number'] = fallback_match.group(4)
        
        # Fallback patterns if the structured approach doesn't work
        if not employee_data['stub_number']:
            stub_match = re.search(r'D\d{6,}', text)
            if stub_match:
                employee_data['stub_number'] = stub_match.group(0)
        
        if not employee_data['period_end']:
            date_matches = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
            if date_matches:
                employee_data['period_end'] = date_matches[-1]  # Last date is often period end
        
        return employee_data
    
    def process_page(self, page_num: int, text: str) -> None:
        """
        Process a single page to extract all data sections.
        
        Args:
            page_num: Page number
            text: Page text content
        """
        print(f"\nProcessing page {page_num}...")
        
        # Extract employee data first
        employee_data = self.extract_employee_data(page_num, text)
        if not employee_data:
            print(f"Page {page_num}: Skipping due to missing employee data")
            return
        
        print(f"Page {page_num}: Employee - {employee_data.employee_name} ({employee_data.employee_number})")
        
        # Extract earnings data
        try:
            earnings_data = extract_earnings_data(text, page_num)
            for earning in earnings_data:
                record = EarningsRecord(
                    employee=employee_data,
                    category=earning.get('category', ''),
                    hours=float(earning.get('hours', 0)),
                    amount=float(earning.get('amount', 0)),
                    ytd=float(earning.get('ytd', 0))
                )
                self.earnings_records.append(record)
            print(f"Page {page_num}: Found {len(earnings_data)} earnings items")
        except Exception as e:
            print(f"Page {page_num}: Error extracting earnings: {e}")
        
        # Extract tax deductions data
        try:
            tax_deductions_data = extract_tax_deductions_data(text, page_num)
            for deduction in tax_deductions_data:
                record = DeductionRecord(
                    employee=employee_data,
                    category=deduction.get('category', ''),
                    amount=float(deduction.get('amount', 0)),
                    ytd=float(deduction.get('ytd', 0))
                )
                self.tax_deductions_records.append(record)
            print(f"Page {page_num}: Found {len(tax_deductions_data)} tax deductions items")
        except Exception as e:
            print(f"Page {page_num}: Error extracting tax deductions: {e}")
        
        # Extract regular deductions data
        try:
            deductions_data = extract_deductions_data(text, page_num)
            for deduction in deductions_data:
                record = DeductionRecord(
                    employee=employee_data,
                    category=deduction.get('category', ''),
                    amount=float(deduction.get('amount', 0)),
                    ytd=float(deduction.get('ytd', 0))
                )
                self.deductions_records.append(record)
            print(f"Page {page_num}: Found {len(deductions_data)} deductions items")
        except Exception as e:
            print(f"Page {page_num}: Error extracting deductions: {e}")
    
    def generate_earnings_csv(self) -> str:
        """Generate earnings.csv with employee data + earnings data."""
        output_file = os.path.join(self.output_dir, "earnings.csv")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'filename', 'page_number', 'employee_name', 'employee_number', 
                'period_end', 'category', 'hours', 'amount', 'ytd'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in self.earnings_records:
                writer.writerow({
                    'filename': self.filename,
                    'page_number': record.employee.page_number,
                    'employee_name': record.employee.employee_name,
                    'employee_number': record.employee.employee_number,
                    'period_end': record.employee.period_end,
                    'category': record.category,
                    'hours': f"{record.hours:.2f}",
                    'amount': f"{record.amount:.2f}",
                    'ytd': f"{record.ytd:.2f}"
                })
        
        print(f"Generated: {output_file} ({len(self.earnings_records)} records)")
        return output_file
    
    def generate_tax_deductions_csv(self) -> str:
        """Generate tax_deductions.csv with employee data + tax deductions data."""
        output_file = os.path.join(self.output_dir, "tax_deductions.csv")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'filename', 'page_number', 'employee_name', 'employee_number', 
                'period_end', 'category', 'amount', 'ytd'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in self.tax_deductions_records:
                writer.writerow({
                    'filename': self.filename,
                    'page_number': record.employee.page_number,
                    'employee_name': record.employee.employee_name,
                    'employee_number': record.employee.employee_number,
                    'period_end': record.employee.period_end,
                    'category': record.category,
                    'amount': f"{record.amount:.2f}",
                    'ytd': f"{record.ytd:.2f}"
                })
        
        print(f"Generated: {output_file} ({len(self.tax_deductions_records)} records)")
        return output_file
    
    def generate_deductions_csv(self) -> str:
        """Generate deductions.csv with employee data + deductions data."""
        output_file = os.path.join(self.output_dir, "deductions.csv")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'filename', 'page_number', 'employee_name', 'employee_number', 
                'period_end', 'category', 'amount', 'ytd'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in self.deductions_records:
                writer.writerow({
                    'filename': self.filename,
                    'page_number': record.employee.page_number,
                    'employee_name': record.employee.employee_name,
                    'employee_number': record.employee.employee_number,
                    'period_end': record.employee.period_end,
                    'category': record.category,
                    'amount': f"{record.amount:.2f}",
                    'ytd': f"{record.ytd:.2f}"
                })
        
        print(f"Generated: {output_file} ({len(self.deductions_records)} records)")
        return output_file
    
    def run(self) -> Dict[str, str]:
        """
        Execute the complete pipeline.
        
        Returns:
            Dictionary with paths to generated CSV files
        """
        print("=" * 60)
        print("PAYSTUB PROCESSING PIPELINE")
        print("=" * 60)
        
        # Step 1: Extract text using pdfplumber
        pages_text = self.extract_text_with_pdfplumber()
        if not pages_text:
            raise ValueError("No text could be extracted from the PDF")
        
        # Step 2: Process each page
        print(f"\nProcessing {len(pages_text)} pages...")
        for page_num, text in pages_text:
            self.process_page(page_num, text)
        
        # Step 3: Generate CSV files
        print(f"\nGenerating CSV files...")
        csv_files = {
            'earnings': self.generate_earnings_csv(),
            'tax_deductions': self.generate_tax_deductions_csv(),
            'deductions': self.generate_deductions_csv()
        }
        
        # Step 4: Summary
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total earnings records: {len(self.earnings_records)}")
        print(f"Total tax deductions records: {len(self.tax_deductions_records)}")
        print(f"Total deductions records: {len(self.deductions_records)}")
        print(f"\nOutput files:")
        for csv_type, csv_path in csv_files.items():
            print(f"  {csv_type}: {csv_path}")
        
        return csv_files


def main():
    """Command-line interface for the paystub pipeline."""
    parser = argparse.ArgumentParser(description="Process paystub PDF and generate CSV files")
    parser.add_argument(
        "input_pdf", 
        nargs="?",
        default=None,
        help="Path to input PDF file (auto-detects from test-files/ if not provided)"
    )
    parser.add_argument(
        "--output-dir", 
        default=None,
        help="Output directory for CSV files (default: result-files/)"
    )
    
    args = parser.parse_args()
    
    try:
        # Get PDF path using utility function
        pdf_path = get_pdf_path(args.input_pdf)
        print(f"Using PDF: {pdf_path}")
        
        # Set up output directory
        output_dir = setup_output_directory(args.output_dir)
        
        # Create and run pipeline
        pipeline = PaystubPipeline(pdf_path, output_dir)
        csv_files = pipeline.run()
        
        print(f"\nPipeline completed successfully!")
        return csv_files
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()