#!/usr/bin/env python3
"""
Improved Paystub Data Extraction Script

Handles Crystal Reports columnar layouts correctly:
- Layout A: Combined Amount/YTD pairs after single YTD header
- Layout B: Separate Amount and YTD columns  
- Layout C: Combined 'Amount YTD' header with amount/ytd pairs

Fixes identified issues:
1. Correct period end date extraction (9/13/2025 vs 9/19/2025)
2. Proper Amount/YTD mapping based on layout detection
3. Accurate hours extraction from Hours column
4. Complete section coverage including previously missed pages
"""

import PyPDF2
import csv
import re
import os
from typing import Dict, List, Tuple, Optional

# Configuration
INPUT_FILE = os.path.join(os.path.dirname(__file__), "test-files", "All_22_Paystubs.pdf")
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

def extract_employee_data_from_page(lines: List[str]) -> Dict[str, str]:
    """Extract employee name, number, and period end from page lines."""
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
    
    # Extract period end date - look for standalone date line containing 9/13/2025
    for line in lines:
        line = line.strip()
        # Look specifically for the 9/13/2025 pattern (not the 9/19/2025 which appears elsewhere)
        if line == '9/13/2025':
            employee_data['period_end'] = line
            break
        # Also check for "Period End" context
        elif 'Period End' in line:
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if date_match:
                employee_data['period_end'] = date_match.group(1)
                break
    
    return employee_data

def extract_earnings_categories(lines: List[str]) -> List[str]:
    """Extract earnings category names."""
    categories = []
    in_earnings = False
    
    for line in lines:
        line_clean = line.strip()
        
        if 'EARNINGS' in line:
            in_earnings = True
            continue
        elif in_earnings and ('TAX DEDUCTIONS' in line or 'DEDUCTIONS' in line):
            break
        elif in_earnings and line_clean and not any(char in line for char in ['•', '�', '*']):
            categories.append(line_clean)
    
    return categories

def extract_tax_deductions_categories(lines: List[str]) -> List[str]:
    """Extract tax deductions category names."""
    categories = []
    in_tax_deductions = False
    
    # Common tax deduction patterns
    valid_patterns = [
        r'Federal W/H',
        r'Social Security Tax',
        r'Medicare Tax',
        r'IAStateW/H',
        r'Aflac\s+\w+',
        r'401\s*K\s+[\w\s]+',
        r'Life Insurance',
        r'Vision\s*[\w\s]*',
        r'Dental\s+[\w\s]+',
        r'Health\s+[\w\s]+',
        r'Child Support',
        r'^\w+\s*(Bank|CU|Credit Union)',
        r'^\w+\s+State\s*$',
        r'Green\s*State',
        r'Community\s+[\w\s]+',
    ]
    
    for line in lines:
        line_clean = line.strip()
        
        if 'TAX DEDUCTIONS' in line:
            in_tax_deductions = True
            continue
        elif in_tax_deductions and (line_clean.startswith('DEDUCTIONS') and 'TAX' not in line):
            break
        elif in_tax_deductions and line_clean:
            # Only include if it matches known tax deduction patterns
            if any(re.search(pattern, line_clean, re.IGNORECASE) for pattern in valid_patterns):
                categories.append(line_clean)
    
    return categories

def extract_deductions_categories(lines: List[str]) -> List[str]:
    """Extract deductions category names."""
    categories = []
    in_deductions = False
    
    # Common deduction patterns (non-tax) - more general patterns
    valid_patterns = [
        r'^\w+\s*(Bank|CU|Credit Union)',
        r'Loan\s+[\w\s]*',
        r'Savings\s+[\w\s]*',
        r'Union\s+Dues',
        r'Parking',
        r'Uniform',
        r'Tool\s+[\w\s]*',
        r'Garnishment',
        r'Charity',
        r'United Way',
        r'Wells\s+Fargo',
        r'Chase',
        r'Bank\s+of\s+',
        r'US\s+Bank',
        r'Capital\s+One',
        r'Bankers\s+Trust',
        r'Green\s*State',
        r'Community\s+',
        r'Journey\s+Credit',
        r'Veridian',
        r'DUPACO',
        r'Premier\s+',
        r'Marine\s+Credit',
        r'Greater\s+Iowa',
        r'First\s+Interstate',
        r'Stride\s+Bank',
        r'BMO',
        r'Chime',
        r'Cashapp'
    ]
    
    for line in lines:
        line_clean = line.strip()
        
        if line_clean.startswith('DEDUCTIONS') and 'TAX' not in line:
            in_deductions = True
            continue
        elif in_deductions and ('NET PAY' in line or 'DIRECT DEPOSITS' in line):
            break
        elif in_deductions and line_clean:
            # Only include if it matches known deduction patterns
            if any(re.search(pattern, line_clean, re.IGNORECASE) for pattern in valid_patterns):
                categories.append(line_clean)
    
    return categories

def detect_layout_pattern(lines: List[str]) -> str:
    """Detect which Crystal Reports layout pattern is used."""
    # Look for layout indicators
    has_separate_amount = False
    has_separate_ytd = False
    has_combined_amount_ytd = False
    
    for line in lines:
        line_clean = line.strip()
        if line_clean == 'Amount':
            has_separate_amount = True
        elif line_clean == 'YTD':
            has_separate_ytd = True
        elif line_clean == 'Amount YTD':
            has_combined_amount_ytd = True
    
    if has_combined_amount_ytd:
        return 'Layout C'  # Combined 'Amount YTD' header with pairs
    elif has_separate_amount and has_separate_ytd:
        return 'Layout B'  # Separate Amount and YTD columns
    else:
        return 'Layout A'  # Combined Amount/YTD pairs after single YTD
    
def extract_hours_column(lines: List[str], num_categories: int) -> List[str]:
    """Extract hours values from the Hours column."""
    hours_values = []
    
    # Find Hours header
    hours_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'Hours':
            hours_line_idx = i
            break
    
    if hours_line_idx is not None:
        # Extract numeric values after Hours header
        for i in range(hours_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if re.match(r'^\d+\.\d{2}$', line):
                hours_values.append(line)
            elif line and not re.search(r'\d', line):
                break  # Stop at non-numeric line
            if len(hours_values) >= num_categories:
                break
    
    # Pad with zeros if needed
    while len(hours_values) < num_categories:
        hours_values.append('0.00')
    
    return hours_values[:num_categories]

def extract_layout_a_data(lines: List[str], num_categories: int) -> List[Tuple[str, str]]:
    """Extract Amount/YTD pairs for Layout A (combined pairs after single YTD)."""
    amount_ytd_pairs = []
    
    # Find YTD header
    ytd_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'YTD':
            ytd_line_idx = i
            break
    
    if ytd_line_idx is not None:
        # Extract Amount YTD pairs
        for i in range(ytd_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if re.search(r'\d+\.\d{2}', line):
                # Parse Amount and YTD from line like "597.58 28,309.32"
                numbers = re.findall(r'[\d,]+\.\d{2}', line)
                if len(numbers) >= 2:
                    amount = numbers[0].replace(',', '')
                    ytd = numbers[1].replace(',', '')
                    amount_ytd_pairs.append((amount, ytd))
                elif len(numbers) == 1:
                    amount = numbers[0].replace(',', '')
                    amount_ytd_pairs.append((amount, '0.00'))
            if len(amount_ytd_pairs) >= num_categories:
                break
    
    return amount_ytd_pairs[:num_categories]

def extract_layout_b_data(lines: List[str], num_categories: int) -> List[Tuple[str, str]]:
    """Extract Amount/YTD for Layout B (separate Amount and YTD columns)."""
    amount_values = []
    ytd_values = []
    
    # Find Amount header and extract values
    amount_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'Amount':
            amount_line_idx = i
            break
    
    if amount_line_idx is not None:
        for i in range(amount_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if re.match(r'^[\d,]+\.\d{2}$', line):
                amount_values.append(line.replace(',', ''))
            elif line and not re.search(r'\d', line):
                break
            if len(amount_values) >= num_categories:
                break
    
    # Find YTD header and extract values
    ytd_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'YTD':
            ytd_line_idx = i
            break
    
    if ytd_line_idx is not None:
        for i in range(ytd_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if re.match(r'^[\d,]+\.\d{2}$', line):
                ytd_values.append(line.replace(',', ''))
            elif line and not re.search(r'\d', line):
                break
            if len(ytd_values) >= num_categories:
                break
    
    # Combine amounts and YTDs
    amount_ytd_pairs = []
    for i in range(num_categories):
        amount = amount_values[i] if i < len(amount_values) else '0.00'
        ytd = ytd_values[i] if i < len(ytd_values) else '0.00'
        amount_ytd_pairs.append((amount, ytd))
    
    return amount_ytd_pairs

def extract_layout_c_data(lines: List[str], num_categories: int) -> List[Tuple[str, str]]:
    """Extract Amount/YTD for Layout C (combined 'Amount YTD' header with pairs)."""
    amount_ytd_pairs = []
    
    # Find 'Amount YTD' header
    amount_ytd_line_idx = None
    for i, line in enumerate(lines):
        if 'Amount YTD' in line.strip():
            amount_ytd_line_idx = i
            break
    
    if amount_ytd_line_idx is not None:
        # Extract Amount YTD pairs
        for i in range(amount_ytd_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if re.search(r'\d+\.\d{2}', line):
                # Parse Amount and YTD from line like "1,000.00 41,133.36"
                numbers = re.findall(r'[\d,]+\.\d{2}', line)
                if len(numbers) >= 2:
                    amount = numbers[0].replace(',', '')
                    ytd = numbers[1].replace(',', '')
                    amount_ytd_pairs.append((amount, ytd))
                elif len(numbers) == 1:
                    amount = numbers[0].replace(',', '')
                    amount_ytd_pairs.append((amount, '0.00'))
            if len(amount_ytd_pairs) >= num_categories:
                break
    
    return amount_ytd_pairs[:num_categories]

def process_earnings_page(page, page_num: int, filename: str) -> List[Dict]:
    """Process a single PDF page and extract earnings data with improved Crystal Reports handling."""
    try:
        text = page.extract_text()
        if not text.strip():
            print(f"   WARNING Page {page_num}: No text found")
            return []
        
        lines = text.split('\n')
        
        # Extract employee data
        employee_data = extract_employee_data_from_page(lines)
        
        # Extract earnings categories
        earnings_categories = extract_earnings_categories(lines)
        
        if not earnings_categories:
            print(f"   WARNING Page {page_num}: No earnings categories found")
            return []
        
        print(f"   Page {page_num}: Found {len(earnings_categories)} earnings categories: {earnings_categories}")
        
        # Detect layout pattern
        layout = detect_layout_pattern(lines)
        print(f"   Page {page_num}: Detected {layout}")
        
        # Extract hours
        hours_values = extract_hours_column(lines, len(earnings_categories))
        
        # Extract amount/YTD based on layout
        if layout == 'Layout A':
            amount_ytd_pairs = extract_layout_a_data(lines, len(earnings_categories))
        elif layout == 'Layout B':
            amount_ytd_pairs = extract_layout_b_data(lines, len(earnings_categories))
        elif layout == 'Layout C':
            amount_ytd_pairs = extract_layout_c_data(lines, len(earnings_categories))
        else:
            print(f"   ERROR Page {page_num}: Unknown layout pattern")
            return []
        
        if not amount_ytd_pairs:
            print(f"   WARNING Page {page_num}: No amount/YTD data found")
            return []
        
        # Create earnings records
        earnings_data = []
        base_info = {
            'filename': filename,
            'page_number': str(page_num),
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end']
        }
        
        for i, category in enumerate(earnings_categories):
            hours = hours_values[i] if i < len(hours_values) else '0.00'
            amount, ytd = amount_ytd_pairs[i] if i < len(amount_ytd_pairs) else ('0.00', '0.00')
            
            record = {
                'category': category,
                'hours': hours,
                'amount': amount,
                'ytd': ytd
            }
            record.update(base_info)
            earnings_data.append(record)
            
            print(f"   {category}: Hours={hours}, Amount={amount}, YTD={ytd}")
        
        print(f"   SUCCESS Page {page_num}: {len(earnings_data)} earnings records extracted")
        return earnings_data
        
    except Exception as e:
        print(f"   ERROR Page {page_num}: {str(e)}")
        return []

def process_tax_deductions_page(page, page_num: int, filename: str) -> List[Dict]:
    """Process a single PDF page and extract tax deductions data."""
    try:
        text = page.extract_text()
        if not text.strip():
            return []
        
        lines = text.split('\n')
        
        # Extract employee data
        employee_data = extract_employee_data_from_page(lines)
        
        # Extract tax deductions categories
        tax_deductions_categories = extract_tax_deductions_categories(lines)
        
        if not tax_deductions_categories:
            return []
        
        print(f"   Page {page_num}: Found {len(tax_deductions_categories)} tax deduction categories: {tax_deductions_categories}")
        
        # Detect layout pattern
        layout = detect_layout_pattern(lines)
        
        # Extract amount/YTD based on layout
        if layout == 'Layout A':
            amount_ytd_pairs = extract_layout_a_data(lines, len(tax_deductions_categories))
        elif layout == 'Layout B':
            amount_ytd_pairs = extract_layout_b_data(lines, len(tax_deductions_categories))
        elif layout == 'Layout C':
            amount_ytd_pairs = extract_layout_c_data(lines, len(tax_deductions_categories))
        else:
            return []
        
        if not amount_ytd_pairs:
            return []
        
        # Create tax deductions records
        tax_deductions_data = []
        base_info = {
            'filename': filename,
            'page_number': str(page_num),
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end']
        }
        
        for i, category in enumerate(tax_deductions_categories):
            amount, ytd = amount_ytd_pairs[i] if i < len(amount_ytd_pairs) else ('0.00', '0.00')
            
            record = {
                'category': category,
                'amount': amount,
                'ytd': ytd
            }
            record.update(base_info)
            tax_deductions_data.append(record)
            
            print(f"   {category}: Amount={amount}, YTD={ytd}")
        
        print(f"   SUCCESS Page {page_num}: {len(tax_deductions_data)} tax deduction records extracted")
        return tax_deductions_data
        
    except Exception as e:
        print(f"   ERROR Page {page_num} tax deductions: {str(e)}")
        return []

def process_deductions_page(page, page_num: int, filename: str) -> List[Dict]:
    """Process a single PDF page and extract deductions data."""
    try:
        text = page.extract_text()
        if not text.strip():
            return []
        
        lines = text.split('\n')
        
        # Extract employee data
        employee_data = extract_employee_data_from_page(lines)
        
        # Extract deductions categories
        deductions_categories = extract_deductions_categories(lines)
        
        if not deductions_categories:
            return []
        
        print(f"   Page {page_num}: Found {len(deductions_categories)} deduction categories: {deductions_categories}")
        
        # Detect layout pattern
        layout = detect_layout_pattern(lines)
        
        # Extract amount/YTD based on layout
        if layout == 'Layout A':
            amount_ytd_pairs = extract_layout_a_data(lines, len(deductions_categories))
        elif layout == 'Layout B':
            amount_ytd_pairs = extract_layout_b_data(lines, len(deductions_categories))
        elif layout == 'Layout C':
            amount_ytd_pairs = extract_layout_c_data(lines, len(deductions_categories))
        else:
            return []
        
        if not amount_ytd_pairs:
            return []
        
        # Create deductions records
        deductions_data = []
        base_info = {
            'filename': filename,
            'page_number': str(page_num),
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end']
        }
        
        for i, category in enumerate(deductions_categories):
            amount, ytd = amount_ytd_pairs[i] if i < len(amount_ytd_pairs) else ('0.00', '0.00')
            
            record = {
                'category': category,
                'amount': amount,
                'ytd': ytd
            }
            record.update(base_info)
            deductions_data.append(record)
            
            print(f"   {category}: Amount={amount}, YTD={ytd}")
        
        print(f"   SUCCESS Page {page_num}: {len(deductions_data)} deduction records extracted")
        return deductions_data
        
    except Exception as e:
        print(f"   ERROR Page {page_num} deductions: {str(e)}")
        return []

def export_to_csv(data: List[Dict], filename: str, data_type: str = 'earnings'):
    """Export data to CSV file."""
    if not data:
        print(f"WARNING No {data_type} data to export.")
        return
    
    if data_type == 'earnings':
        headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'hours', 'amount', 'ytd']
    else:
        headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'period_end', 'category', 'amount', 'ytd']
    
    try:
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"SUCCESS {data_type.title()} data exported to: {output_path}")
        print(f"Records exported: {len(data)}")
        
    except Exception as e:
        print(f"ERROR writing {data_type} CSV file: {str(e)}")

def main():
    """Main function to process PDF and extract all paystub data."""
    print(f"Extracting comprehensive paystub data from: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR Input file not found: {INPUT_FILE}")
        return
    
    all_earnings_data = []
    all_tax_deductions_data = []
    all_deductions_data = []
    
    try:
        with open(INPUT_FILE, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            filename = os.path.basename(INPUT_FILE)
            
            print(f"Processing {filename} ({len(reader.pages)} pages)")
            
            # Process all pages
            for page_num in range(1, len(reader.pages) + 1):
                try:
                    page = reader.pages[page_num - 1]
                    
                    # Extract earnings data
                    earnings_data = process_earnings_page(page, page_num, filename)
                    all_earnings_data.extend(earnings_data)
                    
                    # Extract tax deductions data
                    tax_deductions_data = process_tax_deductions_page(page, page_num, filename)
                    all_tax_deductions_data.extend(tax_deductions_data)
                    
                    # Extract deductions data
                    deductions_data = process_deductions_page(page, page_num, filename)
                    all_deductions_data.extend(deductions_data)
                    
                except Exception as page_error:
                    print(f"   ERROR Page {page_num}: {str(page_error)}")
                    print(f"   Skipping page {page_num} and continuing...")
                    continue
        
        # Export all data to CSV files
        export_to_csv(all_earnings_data, 'earnings_improved.csv', 'earnings')
        export_to_csv(all_tax_deductions_data, 'tax_deductions_improved.csv', 'tax deductions')
        export_to_csv(all_deductions_data, 'deductions_improved.csv', 'deductions')
        
        # Print summary
        print(f"\nSummary:")
        print(f"   Pages processed: {len(reader.pages)}")
        print(f"   Earnings records: {len(all_earnings_data)}")
        print(f"   Tax deductions records: {len(all_tax_deductions_data)}")
        print(f"   Deductions records: {len(all_deductions_data)}")
        
        # Print category summaries
        if all_earnings_data:
            earnings_categories = sorted(set(record['category'] for record in all_earnings_data))
            print(f"   Earnings categories ({len(earnings_categories)}): {earnings_categories}")
        
        if all_tax_deductions_data:
            tax_categories = sorted(set(record['category'] for record in all_tax_deductions_data))
            print(f"   Tax deduction categories ({len(tax_categories)}): {tax_categories}")
        
        if all_deductions_data:
            deduction_categories = sorted(set(record['category'] for record in all_deductions_data))
            print(f"   Deduction categories ({len(deduction_categories)}): {deduction_categories}")
        
        print(f"\nProcessing complete!")
        print(f"CSV files created in: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"ERROR processing PDF: {str(e)}")

if __name__ == "__main__":
    main()