#!/usr/bin/env python3
"""
[DEPRECATED] Comprehensive Paystub Data Extraction Script

DEPRECATED: This script uses PyPDF2 for text extraction. Use paystub_pipeline.py instead,
which uses pdfplumber for better text extraction and structured layout handling.

This script extracts data from all three main sections of paystub PDFs:
1. EARNINGS - categories with Hours, Amount, and YTD
2. TAX DEDUCTIONS - categories with Amount and YTD (no hours)  
3. DEDUCTIONS - categories with Amount and YTD (no hours)

Creates three separate CSV files:
- earnings.csv
- tax_deductions.csv  
- deductions.csv

Each CSV includes employee information (name, number, period end) integrated
from the existing extraction patterns.
"""

import PyPDF2
import csv
import re
import os
from typing import Dict, List, Tuple, Optional
# Import the centralized earnings regex patterns
from regex_patterns.earnings_regex import extract_earnings_data
# Import the centralized deductions regex patterns
from regex_patterns.deductions_regex import extract_tax_deductions_data, extract_deductions_data

# Configuration
INPUT_FILE = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "result-files")

def _is_valid_name(name: str) -> bool:
    """Check if a string looks like a valid employee name."""
    if not name or len(name.strip()) < 3:
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Skip obvious non-names and company indicators
    skip_patterns = [
        r'^\d+$',  # Just numbers
        r'^[^a-zA-Z]*$',  # No letters
        r'Employee',
        r'Number',
        r'Pay\s*Rate',
        r'Hours',
        r'Amount',
        r'YTD',
        r'Period',
        r'End',
        r'Stub',
        r'Social',
        r'Security',
        r'EARNINGS',
        r'DEDUCTIONS',
        r'TAX',
        r'DIRECT',
        r'DEPOSITS',
        r'Inc\.',  # Skip "Inc."
        r'LLC',
        r'Corp',
        r'Company',
        r'Systems',
        r'Window',
        r'Manko',
        r'Hayes\s+Dr',
        r'Box\s+\d+',
        r'P\.O\.',
        r'Manhattan',
        r'Des\s+Moines',
        r'Ave\s*$',
        r'Dr\s*$',
        r'\d{5}',  # ZIP codes
        r'[A-Z]{2}\d{5}',  # State + ZIP
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False
    
    return True

def extract_employee_data_from_page(text: str) -> Dict[str, str]:
    """Extract employee name, number, and period end from page text."""
    lines = text.split('\n')
    
    employee_data = {
        'employee_name': '',
        'employee_number': '',
        'period_end': ''
    }
    
    # Extract employee name (first valid name after company info)
    for line in lines:
        line = line.strip()
        if _is_valid_name(line):
            # Clean up the name
            cleaned_name = re.sub(r'[^\w\s\.]', ' ', line)
            cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
            if _is_valid_name(cleaned_name):
                employee_data['employee_name'] = cleaned_name
                break
    
    # Extract employee number
    for i, line in enumerate(lines):
        if 'Employee Number' in line and i + 1 < len(lines):
            emp_num = lines[i + 1].strip()
            if emp_num and not any(keyword in emp_num.upper() for keyword in ['EARNINGS', 'EMPLOYEE', 'NUMBER']):
                employee_data['employee_number'] = emp_num
                break
    
    # Extract period end date
    for line in lines:
        # Look for date patterns
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
        if date_match:
            # Check if this looks like a period end date (not a random date)
            if 'Period End' in line or len(re.findall(r'\d{1,2}/\d{1,2}/\d{4}', line)) == 1:
                employee_data['period_end'] = date_match.group(1)
                break
    
    return employee_data

def extract_section_categories(lines: List[str], section_name: str) -> List[str]:
    """Extract category names from a specific section."""
    categories = []
    in_section = False
    
    # Define section boundaries
    section_patterns = {
        'EARNINGS': {'start': 'EARNINGS', 'end': 'TAX DEDUCTIONS'},
        'TAX DEDUCTIONS': {'start': 'TAX DEDUCTIONS', 'end': 'DEDUCTIONS'},
        'DEDUCTIONS': {'start': 'DEDUCTIONS', 'end': 'DIRECT DEPOSITS'}
    }
    
    if section_name not in section_patterns:
        return categories
    
    start_pattern = section_patterns[section_name]['start']
    end_pattern = section_patterns[section_name]['end']
    
    # Additional filters for non-category items
    non_category_patterns = [
        r'Check\s+Amount',
        r'Gross\s+Earnings',
        r'Net\s+Earnings',
        r'Period\s+Accrued',
        r'YTD\s+Accrued',
        r'Total\s+Direct',
        r'Total\s+Deductions',
        r'Available\s+PTO',
        r'YTD\s+Paid\s+PTO',
        r'Chime',
        r'Green\s+State',
        r'Marine\s+Credit',
        r'Premier\s+Credit',
        r'Stride\s+Bank',
        r'Veridian\s+Credit',
        r'Wells\s+Fargo',
        r'First\s+Interstate',
        r'Earlham\s+Savings',
        r'\d+\.\d{2}',  # Pure decimal numbers
        r'^\d+$',  # Pure integers
    ]
    
    for line in lines:
        line_clean = line.strip()
        
        # Check for section start
        if start_pattern in line:
            if section_name == 'DEDUCTIONS' and 'TAX' in line:
                continue  # Skip "TAX DEDUCTIONS" when looking for "DEDUCTIONS"
            in_section = True
            continue
        
        # Check for section end
        if in_section and end_pattern in line:
            if section_name == 'TAX DEDUCTIONS' and 'TAX' in line:
                continue  # Don't end on "TAX DEDUCTIONS" header when in TAX section
            break
        
        # Extract categories
        if in_section and line_clean and not any(char in line for char in ['•', '�', '*']):
            # Additional filtering for non-category items
            is_valid_category = True
            for pattern in non_category_patterns:
                if re.search(pattern, line_clean, re.IGNORECASE):
                    is_valid_category = False
                    break
            
            if is_valid_category:
                categories.append(line_clean)
    
    return categories

def extract_data_values(lines: List[str]) -> List[Tuple[str, str]]:
    """Extract Amount and YTD pairs from the data section after YTD header."""
    data_pairs = []
    
    # Find the YTD header line
    ytd_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'YTD':
            ytd_line_idx = i
            break
    
    if ytd_line_idx is None:
        return data_pairs
    
    # Extract data lines after YTD header
    for i in range(ytd_line_idx + 1, len(lines)):
        line = lines[i].strip()
        
        # Look for lines with decimal numbers (Amount YTD pairs)
        if re.search(r'\d+\.\d{2}', line):
            # Parse Amount and YTD from line like "597.58 28,309.32"
            numbers = re.findall(r'[\d,]+\.\d{2}', line)
            if len(numbers) >= 2:
                amount = numbers[0].replace(',', '')
                ytd = numbers[1].replace(',', '')
                data_pairs.append((amount, ytd))
            elif len(numbers) == 1:
                # Single number - could be amount with 0 YTD or vice versa
                amount = numbers[0].replace(',', '')
                data_pairs.append((amount, '0.00'))
        else:
            # Stop when we hit non-numeric data
            break
    
    return data_pairs

def extract_earnings_with_hours(lines: List[str], earnings_categories: List[str], data_pairs: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    """Extract earnings data including hours using centralized patterns."""
    # Reconstruct text from lines to use centralized extraction
    text = '\n'.join(lines)
    earnings_data = extract_earnings_data(text)
    
    # Convert to the format expected by this script
    result = []
    for item in earnings_data:
        result.append({
            'category': item['category'],
            'hours': item['hours'],
            'amount': item['amount'],
            'ytd': item['ytd']
        })
    
    return result

def extract_deductions_data_local(categories: List[str], data_pairs: List[Tuple[str, str]], start_idx: int) -> List[Dict[str, str]]:
    """Extract deduction data (amount and YTD only) for a section."""
    deduction_data = []
    
    for i, category in enumerate(categories):
        data_idx = start_idx + i
        if data_idx < len(data_pairs):
            amount, ytd = data_pairs[data_idx]
            deduction_data.append({
                'category': category,
                'amount': amount,
                'ytd': ytd
            })
    
    return deduction_data

def process_pdf_page(page, page_num: int, filename: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Process a single PDF page and extract all three sections."""
    try:
        text = page.extract_text()
        if not text.strip():
            print(f"   WARNING Page {page_num}: No text found")
            return [], [], []
        
        lines = text.split('\n')
        
        # Extract employee data
        employee_data = extract_employee_data_from_page(text)
        
        # Extract categories from each section
        earnings_categories = extract_section_categories(lines, 'EARNINGS')
        tax_categories = extract_section_categories(lines, 'TAX DEDUCTIONS')
        deduction_categories = extract_section_categories(lines, 'DEDUCTIONS')
        
        print(f"   Page {page_num}: Found {len(earnings_categories)} earnings, {len(tax_categories)} tax deductions, {len(deduction_categories)} deductions")
        
        if not (earnings_categories or tax_categories or deduction_categories):
            print(f"   WARNING Page {page_num}: No categories found in any section")
            return [], [], []
        
        # Extract data values
        data_pairs = extract_data_values(lines)
        
        if not data_pairs:
            print(f"   WARNING Page {page_num}: No financial data found")
            return [], [], []
        
        print(f"   Page {page_num}: Found {len(data_pairs)} data pairs")
        
        # Extract earnings data (with hours)
        earnings_data = extract_earnings_with_hours(lines, earnings_categories, data_pairs)
        
        # Calculate starting indices for other sections
        tax_start_idx = len(earnings_categories)
        deductions_start_idx = tax_start_idx + len(tax_categories)
        
        # Extract tax deductions data
        tax_data = extract_deductions_data_local(tax_categories, data_pairs, tax_start_idx)
        
        # Extract deductions data
        deductions_data = extract_deductions_data_local(deduction_categories, data_pairs, deductions_start_idx)
        
        # Add page and employee info to all records
        base_info = {
            'filename': filename,
            'page_number': str(page_num),
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end']
        }
        
        # Add base info to all records
        for record in earnings_data:
            record.update(base_info)
        
        for record in tax_data:
            record.update(base_info)
            
        for record in deductions_data:
            record.update(base_info)
        
        print(f"   SUCCESS Page {page_num}: {len(earnings_data)} earnings, {len(tax_data)} tax deductions, {len(deductions_data)} deductions extracted")
        
        return earnings_data, tax_data, deductions_data
        
    except Exception as e:
        print(f"ERROR processing page {page_num}: {str(e)}")
        return [], [], []

def export_to_csv(data: List[Dict], filename: str, section_type: str):
    """Export data to CSV file with appropriate headers."""
    if not data:
        print(f"WARNING No {section_type} data to export.")
        return
    
    # Define headers based on section type
    if section_type == 'earnings':
        headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'hours', 'amount', 'ytd']
    else:
        headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'amount', 'ytd']
    
    try:
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"SUCCESS {section_type.title()} data exported to: {output_path}")
        print(f"Records exported: {len(data)}")
        
    except Exception as e:
        print(f"ERROR writing {section_type} CSV file: {str(e)}")

def main():
    """Main function to process PDF and extract all sections."""
    print(f"Extracting comprehensive paystub data from: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR Input file not found: {INPUT_FILE}")
        return
    
    all_earnings_data = []
    all_tax_data = []
    all_deductions_data = []
    
    try:
        with open(INPUT_FILE, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            filename = os.path.basename(INPUT_FILE)
            
            print(f"Processing {filename} ({len(reader.pages)} pages)")
            
            for page_num in range(1, len(reader.pages) + 1):
                try:
                    page = reader.pages[page_num - 1]
                    
                    earnings_data, tax_data, deductions_data = process_pdf_page(page, page_num, filename)
                    
                    all_earnings_data.extend(earnings_data)
                    all_tax_data.extend(tax_data)
                    all_deductions_data.extend(deductions_data)
                    
                except Exception as page_error:
                    print(f"   ERROR Page {page_num}: {str(page_error)}")
                    print(f"   Skipping page {page_num} and continuing...")
                    continue
        
        # Export to CSV files
        export_to_csv(all_earnings_data, 'earnings.csv', 'earnings')
        export_to_csv(all_tax_data, 'tax_deductions.csv', 'tax deductions')
        export_to_csv(all_deductions_data, 'deductions.csv', 'deductions')
        
        # Print summary
        print(f"\nSummary:")
        print(f"   Pages processed: {len(reader.pages)}")
        print(f"   Earnings records: {len(all_earnings_data)}")
        print(f"   Tax deduction records: {len(all_tax_data)}")
        print(f"   Deduction records: {len(all_deductions_data)}")
        
        # Get unique categories for each section
        if all_earnings_data:
            earnings_categories = sorted(set(record['category'] for record in all_earnings_data))
            print(f"   Unique earnings categories: {len(earnings_categories)}")
            
        if all_tax_data:
            tax_categories = sorted(set(record['category'] for record in all_tax_data))
            print(f"   Unique tax deduction categories: {len(tax_categories)}")
            
        if all_deductions_data:
            deduction_categories = sorted(set(record['category'] for record in all_deductions_data))
            print(f"   Unique deduction categories: {len(deduction_categories)}")
        
        print(f"\nProcessing complete!")
        print(f"CSV files created in: {OUTPUT_DIR}")
        
    except FileNotFoundError:
        print(f"ERROR Input file not found: {INPUT_FILE}")
    except Exception as e:
        print(f"ERROR processing PDF: {str(e)}")

if __name__ == "__main__":
    main()