import os
import re
import json
import sys
import pdfplumber
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from dataclasses import field
# Import the centralized employee regex patterns
from regex_patterns.employee_regex import extract_employee_data_patterns

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import LOCAL_DESKTOP_TEMP

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_DIR = TEST_FILES_DIR

@dataclass
class PaystubItem:
    """Represents a single line item in a paystub section."""
    name: str
    hours: Optional[float] = None
    amount: float = 0.0
    ytd: float = 0.0

@dataclass
class PaystubData:
    """Represents the extracted data from a paystub."""
    employee_name: str = ""
    employee_number: str = ""
    pay_period_end: str = ""
    stub_number: str = ""
    pay_rate: str = ""
    earnings: List[PaystubItem] = field(default_factory=list)
    tax_deductions: List[PaystubItem] = field(default_factory=list)
    deductions: List[PaystubItem] = field(default_factory=list)
    direct_deposits: List[PaystubItem] = field(default_factory=list)
    gross_earnings: float = 0.0
    net_earnings: float = 0.0
    total_deductions: float = 0.0

class PaystubExtractor:
    """Extracts structured data from paystub text using pdfplumber + regex."""
    
    def __init__(self):
        # Regex patterns for different sections
        self.section_patterns = {
            'earnings': r'•••\s*EARNINGS\s*•••',
            'tax_deductions': r'•••\s*TAX\s+DEDUCTIONS\s*•••',
            'deductions': r'•••\s*DEDUCTIONS\s*\*+',
            'direct_deposits': r'•••\s*DIRECT\s+DEPOSITS\s*•••'
        }
        
        # Pattern to match line items with amounts
        # Matches: "Item Name" followed by optional hours, amount, YTD
        self.line_item_pattern = r'^([A-Za-z][A-Za-z\s\-/\.()&]+?)\s+(?:(\d+\.\d+)\s+)?(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)$'
        
        # Pattern for summary amounts
        self.summary_patterns = {
            'gross_earnings': r'Gross\s+Earnings:\s*([\d,]+\.\d+)',
            'net_earnings': r'Net\s+Earnings:\s*([\d,]+\.\d+)',
            'total_deductions': r'Total\s+Deductions:\s*([\d,]+\.\d+)'
        }

    def extract_text_from_page(self, page):
        """Extract clean text using pdfplumber's optimized method."""
        try:
            if hasattr(page, 'extract_text_lines'):
                text_lines = page.extract_text_lines(
                    layout=True,
                    x_tolerance=3,
                    y_tolerance=3
                )
                lines = []
                for line in text_lines:
                    text = line.get('text', '').strip()
                    if text:
                        lines.append(text)
                return '\n'.join(lines)
            else:
                return page.extract_text(
                    x_tolerance=3,
                    y_tolerance=3,
                    layout=True,
                    x_density=7.25,
                    y_density=13
                )
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def clean_amount(self, amount_str: str) -> float:
        """Clean and convert amount string to float."""
        if not amount_str:
            return 0.0
        # Remove commas and convert to float
        cleaned = amount_str.replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def extract_employee_info(self, text: str) -> Dict[str, str]:
        """Extract employee information using centralized regex patterns"""
        # Use the centralized extraction function
        employee_data = extract_employee_data_patterns(text, page_num=1)
        
        # Convert to the expected format for this function
        info = {
            'employee_name': employee_data.get('employee_name', ''),
            'employee_number': employee_data.get('employee_number', ''),
            'pay_rate': employee_data.get('pay_rate', ''),
            'period_end': employee_data.get('period_end', ''),
            'stub_number': employee_data.get('stub_number', '')
        }
        
        return info

    def extract_section_items(self, text: str, section_name: str) -> List[PaystubItem]:
        """Extract items from a specific section."""
        items = []
        
        # Find the section start
        section_pattern = self.section_patterns.get(section_name)
        if not section_pattern:
            return items
        
        lines = text.split('\n')
        in_section = False
        
        for line in lines:
            # Check if we're starting a new section
            if re.search(section_pattern, line, re.IGNORECASE):
                in_section = True
                continue
            
            # Check if we've hit another section (end current section)
            if in_section and any(re.search(pattern, line, re.IGNORECASE) 
                                for pattern in self.section_patterns.values()
                                if pattern != section_pattern):
                break
            
            # If we're in the section, try to parse line items
            if in_section:
                # Try to match line items with amounts
                match = re.search(self.line_item_pattern, line.strip())
                if match:
                    name = match.group(1).strip()
                    hours_str = match.group(2)
                    amount_str = match.group(3)
                    ytd_str = match.group(4)
                    
                    # Skip lines that look like headers
                    if name.lower() in ['hours', 'amount', 'ytd']:
                        continue
                    
                    item = PaystubItem(
                        name=name,
                        hours=float(hours_str) if hours_str else None,
                        amount=self.clean_amount(amount_str),
                        ytd=self.clean_amount(ytd_str)
                    )
                    items.append(item)
        
        return items

    def extract_summary_amounts(self, text: str) -> Dict[str, float]:
        """Extract summary amounts from the paystub."""
        amounts = {}
        
        for key, pattern in self.summary_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts[key] = self.clean_amount(match.group(1))
        
        return amounts

    def extract_paystub_data(self, page) -> PaystubData:
        """Extract complete paystub data from a page."""
        # Get clean text
        text = self.extract_text_from_page(page)
        
        if not text:
            return PaystubData()
        
        # Extract employee info
        employee_info = self.extract_employee_info(text)
        
        # Extract sections
        earnings = self.extract_section_items(text, 'earnings')
        tax_deductions = self.extract_section_items(text, 'tax_deductions')
        deductions = self.extract_section_items(text, 'deductions')
        direct_deposits = self.extract_section_items(text, 'direct_deposits')
        
        # Extract summary amounts
        summary = self.extract_summary_amounts(text)
        
        # Create PaystubData object
        paystub = PaystubData(
            employee_name=employee_info.get('employee_name', ''),
            employee_number=employee_info.get('employee_number', ''),
            pay_period_end=employee_info.get('period_end', ''),
            stub_number=employee_info.get('stub_number', ''),
            pay_rate=employee_info.get('pay_rate', ''),
            earnings=earnings,
            tax_deductions=tax_deductions,
            deductions=deductions,
            direct_deposits=direct_deposits,
            gross_earnings=summary.get('gross_earnings', 0.0),
            net_earnings=summary.get('net_earnings', 0.0),
            total_deductions=summary.get('total_deductions', 0.0)
        )
        
        return paystub

def main():
    """Process PDF files and extract structured paystub data."""
    extractor = PaystubExtractor()
    
    if not os.path.exists(INPUT_DIR):
        print(f"Input directory does not exist: {INPUT_DIR}")
        return
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in: {INPUT_DIR}")
        return
    
    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        print(f"\n{'='*80}")
        print(f"Processing: {filename}")
        print('='*80)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Process first 3 pages for testing
                for i, page in enumerate(pdf.pages[:3], start=1):
                    print(f"\n--- Page {i} ---")
                    paystub_data = extractor.extract_paystub_data(page)
                    
                    # Print extracted data
                    print(f"Employee: {paystub_data.employee_name}")
                    print(f"Employee #: {paystub_data.employee_number}")
                    print(f"Pay Period End: {paystub_data.pay_period_end}")
                    print(f"Stub #: {paystub_data.stub_number}")
                    print(f"Pay Rate: {paystub_data.pay_rate}")
                    
                    print(f"\nEARNINGS ({len(paystub_data.earnings)} items):")
                    for item in paystub_data.earnings:
                        hours_str = f"{item.hours:6.2f}" if item.hours is not None else "  --  "
                        print(f"  {item.name:<25} {hours_str} ${item.amount:8.2f} ${item.ytd:10.2f}")
                    
                    print(f"\nTAX DEDUCTIONS ({len(paystub_data.tax_deductions)} items):")
                    for item in paystub_data.tax_deductions:
                        print(f"  {item.name:<25} ${item.amount:8.2f} ${item.ytd:10.2f}")
                    
                    print(f"\nDEDUCTIONS ({len(paystub_data.deductions)} items):")
                    for item in paystub_data.deductions:
                        print(f"  {item.name:<25} ${item.amount:8.2f} ${item.ytd:10.2f}")
                    
                    print(f"\nSUMMARY:")
                    print(f"  Gross Earnings: ${paystub_data.gross_earnings:10.2f}")
                    print(f"  Total Deductions: ${paystub_data.total_deductions:8.2f}")
                    print(f"  Net Earnings: ${paystub_data.net_earnings:12.2f}")
                    
                    # Save to JSON for further processing
                    output_file = f"paystub_page_{i}.json"
                    with open(output_file, 'w') as f:
                        json.dump(asdict(paystub_data), f, indent=2)
                    print(f"\nData saved to: {output_file}")
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()