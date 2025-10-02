import os
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_FILE = os.path.join(TEST_FILES_DIR, "All_22_Paystubs.pdf")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "result-files", "earnings.csv")

def extract_employee_data_from_page(text):
    """Extract employee data from a single page of text using patterns from extract-paystub-data.py"""
    # Initialize data dictionary
    data = {
        'employee_name': '',
        'employee_number': '',
        'period_end': ''
    }
    
    # Utility: validate candidate name (kept lightweight to avoid false positives)
    def _is_valid_name(name: str) -> bool:
        if not name:
            return False
        if any(ch.isdigit() for ch in name):  # reject if digits inside
            return False
        tokens = [t for t in name.replace(',', ' ').split() if t]
        if len(tokens) < 2 or len(tokens) > 7:
            return False
        # Require at least one token length > 1 (avoid just initials) and one capitalized word
        if not any(len(t.strip(".-")) > 1 for t in tokens):
            return False
        if not any(t[0].isupper() for t in tokens if t):
            return False
        # Suffix allowance
        suffixes = {"JR", "SR", "II", "III", "IV", "V"}
        # Remove periods for suffix compare
        if tokens[-1].rstrip('.').upper() in suffixes and len(tokens) < 2:
            return False
        # Reasonable total length
        if not (5 < len(name) < 60):
            return False
        return True

    # Extract employee name (formatted layout - look for name after company address block)
    # Enhanced pattern: allows hyphens, apostrophes, commas, suffixes
    # Anchor: state abbreviation + ZIP then newline then the name line
    name_pattern_1 = r"[A-Z]{2}\s+\d{5}\s*\n([A-Za-z][A-Za-z\.\'\ \- ,]{3,60}?)(?:,\s*(?:Jr|Sr|II|III|IV|V))?\s*\n"
    name_match = re.search(name_pattern_1, text)
    if name_match:
        candidate_name = name_match.group(1).strip()
        if _is_valid_name(candidate_name):
            data['employee_name'] = candidate_name
    
    # Extract employee number (formatted layout: "Employee Number \n00-ANA")
    emp_pattern_1 = r'Employee Number\s*\n([0-9]{2}-[A-Z]+)'
    emp_match = re.search(emp_pattern_1, text)
    if emp_match:
        data['employee_number'] = emp_match.group(1).strip()
    
    # Extract period end date (standard layout newline)
    period_end_pattern_1 = r'Period End\s*\n(\d{1,2}/\d{1,2}/\d{4})'
    period_end_match = re.search(period_end_pattern_1, text)
    if period_end_match:
        data['period_end'] = period_end_match.group(1).strip()
    
    # Fallback patterns if primary patterns don't work
    if not data['employee_name']:
        # Pattern: Look for name after date - enhanced character class & optional suffix
        name_pattern_2 = r"\d{1,2}/\d{1,2}/\d{4}\s+([A-Za-z][A-Za-z\.\'\ \- ,]{3,60}?)(?:,\s*(?:Jr|Sr|II|III|IV|V))?\s*\n"
        name_match = re.search(name_pattern_2, text)
        if name_match:
            candidate_name = name_match.group(1).strip()
            if _is_valid_name(candidate_name):
                data['employee_name'] = candidate_name
        
        # Fallback heuristic: scan lines between header and "Employee Number"
        if not data['employee_name']:
            lines = text.splitlines()
            try:
                header_end_idx = 0
                for i, ln in enumerate(lines[:10]):  # search first 10 lines for ZIP (5 digits)
                    if re.search(r'\b\d{5}\b', ln):
                        header_end_idx = i
                emp_idx = next((i for i, ln in enumerate(lines) if 'Employee Number' in ln), None)
                window = lines[header_end_idx+1:emp_idx if emp_idx else header_end_idx+6]
                for cand in window:
                    c = cand.strip()
                    if _is_valid_name(c):
                        data['employee_name'] = c
                        break
            except Exception:
                pass
    
    # Extract employee number (compact layout: "YTD20-XXX" format)
    if not data['employee_number']:
        emp_pattern_2 = r'YTD([0-9]{2}-[A-Z]+[0-9]*)'
        emp_match = re.search(emp_pattern_2, text)
        if emp_match:
            data['employee_number'] = emp_match.group(1).strip()
    
    # Extract period end date fallback patterns
    if not data['period_end']:
        # Look for merged line: "Period End Stub Number" style
        merged_pattern = r'(?:Period End\s+Stub Number|Period End Stub Number)?\s*(\d{1,2}/\d{1,2}/\d{4})\s+D\d{6,}'
        merged_match = re.search(merged_pattern, text)
        if merged_match:
            data['period_end'] = merged_match.group(1)
    
    if not data['period_end']:
        # Compact layout inline before labels
        period_end_pattern_2 = r'(\d{1,2}/\d{1,2}/\d{4}).{0,40}?Period End'
        period_end_match = re.search(period_end_pattern_2, text)
        if period_end_match:
            data['period_end'] = period_end_match.group(1).strip()
    
    if not data['period_end']:
        # Fallback: choose date closest to 'Pay Rate' or 'Stub Number'
        dates = list(re.finditer(r'\b\d{1,2}/\d{1,2}/\d{4}\b', text))
        if dates:
            anchor_indices = []
            for anchor in ('Pay Rate', 'Stub Number'):
                idx = text.find(anchor)
                if idx != -1:
                    anchor_indices.append(idx)
            if anchor_indices:
                target = min(anchor_indices)
                # Pick date whose start position absolute distance to anchor is minimal
                best = min(dates, key=lambda m: abs(m.start() - target))
                data['period_end'] = best.group(0)
            else:
                # Default: first date (often correct for period end in top block)
                data['period_end'] = dates[0].group(0)
    
    return data

def extract_earnings_from_page(text, filename, page_num):
    """Extract earnings data from a single page of text"""
    lines = text.split('\n')
    
    # Initialize result list for this page
    page_earnings = []
    
    # Extract employee data for this page
    employee_data = extract_employee_data_from_page(text)
    
    # Find EARNINGS section
    earnings_start = -1
    earnings_end = -1
    
    for i, line in enumerate(lines):
        if "EARNINGS" in line and earnings_start == -1:
            earnings_start = i
        elif earnings_start != -1 and ("TAX DEDUCTIONS" in line or "DEDUCTIONS" in line):
            earnings_end = i
            break
    
    if earnings_start == -1:
        print(f"   WARNING Page {page_num}: No EARNINGS section found")
        return []
    
    earnings_end = earnings_end if earnings_end > 0 else len(lines)
    
    # Extract earnings categories
    earnings_categories = []
    for i in range(earnings_start + 1, earnings_end):
        line = lines[i].strip()
        if line and not line.startswith('***') and not line.startswith('���'):
            earnings_categories.append(line)
    
    if not earnings_categories:
        print(f"   WARNING Page {page_num}: No earnings categories found")
        return []
    
    print(f"   Categories: Found {len(earnings_categories)} categories: {earnings_categories}")
    
    # Find the Hours column data
    hours_data = []
    hours_line_idx = -1
    
    # Look for "Hours" header
    for i, line in enumerate(lines):
        if line.strip() == "Hours":
            hours_line_idx = i
            break
    
    if hours_line_idx >= 0:
        # Collect hours data from the lines following the Hours header
        for i in range(hours_line_idx + 1, min(hours_line_idx + 1 + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            # Extract decimal number from the line
            hour_match = re.search(r'\d+\.\d+', line)
            if hour_match:
                hours_data.append(hour_match.group())
            else:
                hours_data.append("0.00")
    
    # Find Amount and YTD data - handle both layout types
    amount_ytd_data = []
    amount_line_idx = -1
    ytd_line_idx = -1
    
    # Look for "Amount" and "YTD" headers
    for i, line in enumerate(lines):
        if line.strip() == "Amount" and amount_line_idx == -1:
            amount_line_idx = i
        if line.strip() == "YTD" and ytd_line_idx == -1:
            ytd_line_idx = i
    
    # Check which layout pattern we have
    if amount_line_idx >= 0 and ytd_line_idx >= 0:
        # Layout Type 2: Separate Amount and YTD headers (like Page 2)
        print(f"   Layout: Using separate Amount/YTD headers layout")
        
        # Extract Amount data
        amount_data = []
        for i in range(amount_line_idx + 1, min(amount_line_idx + 1 + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            amount_match = re.search(r'\d+(?:,\d{3})*\.?\d*', line)
            if amount_match:
                amount_data.append(amount_match.group().replace(',', ''))
            else:
                amount_data.append("0.00")
        
        # Extract YTD data
        ytd_data = []
        for i in range(ytd_line_idx + 1, min(ytd_line_idx + 1 + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            ytd_match = re.search(r'\d+(?:,\d{3})*\.?\d*', line)
            if ytd_match:
                ytd_data.append(ytd_match.group().replace(',', ''))
            else:
                ytd_data.append("0.00")
        
        # Combine amount and YTD data
        for i in range(len(earnings_categories)):
            amount = amount_data[i] if i < len(amount_data) else "0.00"
            ytd = ytd_data[i] if i < len(ytd_data) else "0.00"
            amount_ytd_data.append((amount, ytd))
            
    elif ytd_line_idx >= 0:
        # Layout Type 1: Combined Amount and YTD pairs after YTD header (like Page 1)
        print(f"   Layout: Using combined Amount/YTD pairs layout")
        
        # The data starts after the YTD header
        data_start = ytd_line_idx + 1
        for i in range(data_start, min(data_start + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            # Extract two decimal numbers from each line (Amount and YTD)
            numbers = re.findall(r'\d+(?:,\d{3})*\.?\d*', line)
            if len(numbers) >= 2:
                # Remove commas for proper decimal conversion
                amount = numbers[0].replace(',', '')
                ytd = numbers[1].replace(',', '')
                amount_ytd_data.append((amount, ytd))
            else:
                amount_ytd_data.append(("0.00", "0.00"))
    else:
        # Fallback: no clear pattern found
        print(f"   Warning: No clear Amount/YTD pattern found")
        for i in range(len(earnings_categories)):
            amount_ytd_data.append(("0.00", "0.00"))
    
    # Match categories with their data
    for i, category in enumerate(earnings_categories):
        hours = hours_data[i] if i < len(hours_data) else "0.00"
        amount, ytd = amount_ytd_data[i] if i < len(amount_ytd_data) else ("0.00", "0.00")
        
        earnings_record = {
            'filename': filename,
            'page_number': page_num,
            'employee_name': employee_data['employee_name'],
            'employee_number': employee_data['employee_number'],
            'period_end': employee_data['period_end'],
            'category': category,
            'hours': hours,
            'amount': amount,
            'ytd': ytd
        }
        
        page_earnings.append(earnings_record)
        print(f"   {category}: Hours={hours}, Amount={amount}, YTD={ytd}")
    
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
