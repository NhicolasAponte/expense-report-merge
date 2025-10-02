"""
Centralized regex patterns for earnings data extraction from paystub PDFs.

This module contains all earnings-related regex patterns and extraction logic
used across the paystub processing scripts, eliminating redundancy and improving maintainability.
"""

import re
from typing import Dict, List, Tuple, Optional, Any


class EarningsRegexPatterns:
    """Centralized container for all earnings-related regex patterns."""
    
    # Section boundary patterns
    EARNINGS_SECTION_START = r'•••\s*EARNINGS\s*•••|EARNINGS'
    EARNINGS_SECTION_END = r'•••\s*TAX\s+DEDUCTIONS\s*•••|TAX DEDUCTIONS|DEDUCTIONS'
    
    # Header patterns for different layout types
    HOURS_HEADER = r'^Hours$'
    AMOUNT_HEADER = r'^Amount$'
    YTD_HEADER = r'^YTD$'
    
    # Data extraction patterns
    DECIMAL_NUMBER = r'\d+\.\d+'
    CURRENCY_AMOUNT = r'\d+(?:,\d{3})*\.?\d*'
    HOURS_VALUE = r'^\d+\.\d{2}$'
    
    # Line item patterns (for structured extraction)
    LINE_ITEM_WITH_HOURS = r'^([A-Za-z][A-Za-z\s\-/\.()&]+?)\s+(?:(\d+\.\d+)\s+)?(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)$'
    
    # Summary patterns
    GROSS_EARNINGS = r'Gross\s+Earnings:\s*([\d,]+\.\d+)'
    NET_EARNINGS = r'Net\s+Earnings:\s*([\d,]+\.\d+)'
    TOTAL_DEDUCTIONS = r'Total\s+Deductions:\s*([\d,]+\.\d+)'
    
    # Category name patterns (to filter out non-category lines)
    VALID_CATEGORY = r'^[A-Za-z][A-Za-z\s\-/\.()&]+$'
    SKIP_PATTERNS = [
        r'^\*+$',           # Lines with only asterisks
        r'^•+$',            # Lines with only bullets
        r'^\s*$',           # Empty lines
        r'Hours|Amount|YTD', # Header lines
        r'Gross|Net|Total'   # Summary lines
    ]


class EarningsDataExtractor:
    """Handles earnings data extraction using centralized patterns."""
    
    def __init__(self):
        self.patterns = EarningsRegexPatterns()
    
    def find_earnings_section(self, lines: List[str]) -> Tuple[int, int]:
        """
        Find the start and end indices of the EARNINGS section.
        
        Args:
            lines: List of text lines from the paystub
            
        Returns:
            Tuple of (start_idx, end_idx) where -1 indicates not found
        """
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if re.search(self.patterns.EARNINGS_SECTION_START, line, re.IGNORECASE) and start_idx == -1:
                start_idx = i
            elif start_idx != -1 and re.search(self.patterns.EARNINGS_SECTION_END, line, re.IGNORECASE):
                end_idx = i
                break
        
        if start_idx != -1 and end_idx == -1:
            end_idx = len(lines)
            
        return start_idx, end_idx
    
    def extract_earnings_categories(self, lines: List[str], start_idx: int, end_idx: int) -> List[str]:
        """
        Extract earnings category names from the EARNINGS section.
        
        Args:
            lines: List of text lines from the paystub
            start_idx: Start index of EARNINGS section
            end_idx: End index of EARNINGS section
            
        Returns:
            List of category names
        """
        categories = []
        
        for i in range(start_idx + 1, end_idx):
            line = lines[i].strip()
            
            # Skip empty lines and header patterns
            if not line or any(re.search(pattern, line, re.IGNORECASE) for pattern in self.patterns.SKIP_PATTERNS):
                continue
                
            # Check if line looks like a valid category name
            if re.match(self.patterns.VALID_CATEGORY, line):
                categories.append(line)
        
        return categories
    
    def find_column_data(self, lines: List[str], header_pattern: str, num_items: int) -> List[str]:
        """
        Find and extract data from a specific column (Hours, Amount, or YTD).
        
        Args:
            lines: List of text lines from the paystub
            header_pattern: Regex pattern for the column header
            num_items: Expected number of data items to extract
            
        Returns:
            List of extracted values
        """
        data = []
        header_idx = -1
        
        # Find the header
        for i, line in enumerate(lines):
            if re.match(header_pattern, line.strip()):
                header_idx = i
                break
        
        if header_idx == -1:
            return ['0.00'] * num_items
        
        # Extract data from lines following the header
        for i in range(header_idx + 1, min(header_idx + 1 + num_items, len(lines))):
            line = lines[i].strip()
            
            # Extract number from the line
            if header_pattern == self.patterns.HOURS_HEADER:
                match = re.search(self.patterns.DECIMAL_NUMBER, line)
            else:
                match = re.search(self.patterns.CURRENCY_AMOUNT, line)
            
            if match:
                data.append(match.group().replace(',', ''))
            else:
                data.append('0.00')
        
        # Pad with zeros if needed
        while len(data) < num_items:
            data.append('0.00')
            
        return data
    
    def detect_layout_type(self, lines: List[str]) -> str:
        """
        Detect which layout type the paystub is using.
        
        Args:
            lines: List of text lines from the paystub
            
        Returns:
            'separate_headers' for Amount/YTD separate headers
            'combined_pairs' for combined Amount/YTD pairs after YTD header
            'structured' for structured line items with embedded amounts
        """
        has_amount_header = any(re.match(self.patterns.AMOUNT_HEADER, line.strip()) for line in lines)
        has_ytd_header = any(re.match(self.patterns.YTD_HEADER, line.strip()) for line in lines)
        
        if has_amount_header and has_ytd_header:
            return 'separate_headers'
        elif has_ytd_header:
            return 'combined_pairs'
        else:
            return 'structured'
    
    def extract_combined_amount_ytd_pairs(self, lines: List[str], ytd_header_idx: int, num_items: int) -> List[Tuple[str, str]]:
        """
        Extract Amount/YTD pairs from combined layout (two numbers per line).
        
        Args:
            lines: List of text lines from the paystub
            ytd_header_idx: Index of the YTD header line
            num_items: Expected number of data pairs to extract
            
        Returns:
            List of (amount, ytd) tuples
        """
        pairs = []
        
        for i in range(ytd_header_idx + 1, min(ytd_header_idx + 1 + num_items, len(lines))):
            line = lines[i].strip()
            
            # Extract two numbers from each line
            numbers = re.findall(self.patterns.CURRENCY_AMOUNT, line)
            if len(numbers) >= 2:
                amount = numbers[0].replace(',', '')
                ytd = numbers[1].replace(',', '')
                pairs.append((amount, ytd))
            else:
                pairs.append(('0.00', '0.00'))
        
        # Pad with zeros if needed
        while len(pairs) < num_items:
            pairs.append(('0.00', '0.00'))
            
        return pairs
    
    def extract_structured_line_items(self, lines: List[str], start_idx: int, end_idx: int) -> List[Dict[str, str]]:
        """
        Extract earnings from structured line items (name + amounts on same line).
        
        Args:
            lines: List of text lines from the paystub
            start_idx: Start index of EARNINGS section
            end_idx: End index of EARNINGS section
            
        Returns:
            List of dictionaries with category, hours, amount, ytd
        """
        items = []
        
        for i in range(start_idx + 1, end_idx):
            line = lines[i].strip()
            
            # Try to match the structured line item pattern
            match = re.match(self.patterns.LINE_ITEM_WITH_HOURS, line)
            if match:
                category = match.group(1).strip()
                hours = match.group(2) if match.group(2) else '0.00'
                amount = match.group(3).replace(',', '') if match.group(3) else '0.00'
                ytd = match.group(4).replace(',', '') if match.group(4) else '0.00'
                
                items.append({
                    'category': category,
                    'hours': hours,
                    'amount': amount,
                    'ytd': ytd
                })
        
        return items
    
    def clean_amount(self, amount_str: str) -> float:
        """
        Clean and convert amount string to float.
        
        Args:
            amount_str: String representation of amount
            
        Returns:
            Float value of the amount
        """
        if not amount_str:
            return 0.0
        
        cleaned = amount_str.replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def extract_summary_amounts(self, text: str) -> Dict[str, float]:
        """
        Extract summary amounts (Gross Earnings, Net Earnings, Total Deductions).
        
        Args:
            text: Full text content of the paystub page
            
        Returns:
            Dictionary with summary amounts
        """
        summary = {
            'gross_earnings': 0.0,
            'net_earnings': 0.0,
            'total_deductions': 0.0
        }
        
        # Extract gross earnings
        gross_match = re.search(self.patterns.GROSS_EARNINGS, text)
        if gross_match:
            summary['gross_earnings'] = self.clean_amount(gross_match.group(1))
        
        # Extract net earnings
        net_match = re.search(self.patterns.NET_EARNINGS, text)
        if net_match:
            summary['net_earnings'] = self.clean_amount(net_match.group(1))
        
        # Extract total deductions
        deductions_match = re.search(self.patterns.TOTAL_DEDUCTIONS, text)
        if deductions_match:
            summary['total_deductions'] = self.clean_amount(deductions_match.group(1))
        
        return summary


def extract_earnings_data(text: str, page_num: int = 1) -> List[Dict[str, Any]]:
    """
    Main function to extract earnings data, auto-detecting format (pdfplumber vs PyPDF2).
    
    Args:
        text: Full text content of the paystub page
        page_num: Page number for reference
        
    Returns:
        List of earnings records with category, hours, amount, ytd
    """
    # Try pdfplumber format first (more structured)
    pdfplumber_result = extract_earnings_data_pdfplumber(text, page_num)
    if pdfplumber_result:
        return pdfplumber_result
    
    # Fallback to original PyPDF2 format extraction
    extractor = EarningsDataExtractor()
    lines = text.split('\n')
    
    # Find earnings section
    start_idx, end_idx = extractor.find_earnings_section(lines)
    if start_idx == -1:
        return []
    
    # Extract categories
    categories = extractor.extract_earnings_categories(lines, start_idx, end_idx)
    if not categories:
        return []
    
    # Detect layout type and extract accordingly
    layout_type = extractor.detect_layout_type(lines)
    
    if layout_type == 'structured':
        # Extract from structured line items
        return extractor.extract_structured_line_items(lines, start_idx, end_idx)
    
    elif layout_type == 'separate_headers':
        # Extract from separate Hours, Amount, YTD headers
        hours_data = extractor.find_column_data(lines, extractor.patterns.HOURS_HEADER, len(categories))
        amount_data = extractor.find_column_data(lines, extractor.patterns.AMOUNT_HEADER, len(categories))
        ytd_data = extractor.find_column_data(lines, extractor.patterns.YTD_HEADER, len(categories))
        
        earnings = []
        for i, category in enumerate(categories):
            earnings.append({
                'category': category,
                'hours': hours_data[i] if i < len(hours_data) else '0.00',
                'amount': amount_data[i] if i < len(amount_data) else '0.00',
                'ytd': ytd_data[i] if i < len(ytd_data) else '0.00'
            })
        return earnings
    
    elif layout_type == 'combined_pairs':
        # Extract from combined Amount/YTD pairs after YTD header
        hours_data = extractor.find_column_data(lines, extractor.patterns.HOURS_HEADER, len(categories))
        
        # Find YTD header index
        ytd_idx = -1
        for i, line in enumerate(lines):
            if re.match(extractor.patterns.YTD_HEADER, line.strip()):
                ytd_idx = i
                break
        
        if ytd_idx != -1:
            amount_ytd_pairs = extractor.extract_combined_amount_ytd_pairs(lines, ytd_idx, len(categories))
            
            earnings = []
            for i, category in enumerate(categories):
                amount, ytd = amount_ytd_pairs[i] if i < len(amount_ytd_pairs) else ('0.00', '0.00')
                earnings.append({
                    'category': category,
                    'hours': hours_data[i] if i < len(hours_data) else '0.00',
                    'amount': amount,
                    'ytd': ytd
                })
            return earnings
    
    return []


def extract_earnings_data_pdfplumber(text: str, page_num: int = 1) -> List[Dict[str, Any]]:
    """
    Extract earnings data from pdfplumber text format.
    
    pdfplumber format: "Category Hours Amount YTD" all on one line
    Examples:
    - "Holiday 0.00 0.00 1,428.00"
    - "Loaders 29.15 597.58 28,309.32"
    - "Paid Time Off 14.00 287.00 1,598.00"
    
    Args:
        text: Full text content from pdfplumber
        page_num: Page number for reference
        
    Returns:
        List of earnings records with category, hours, amount, ytd
    """
    lines = text.split('\n')
    earnings = []
    
    # Find earnings section boundaries
    earnings_start = -1
    earnings_end = -1
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Look for earnings section start - handle all format variations including mixed patterns
        if (('•••EARNINGS•••' in line_stripped or '••• EARNINGS •••' in line_stripped or 
             '***EARNINGS***' in line_stripped or '*** EARNINGS ***' in line_stripped or
             '***EARNINGS•••' in line_stripped or '•••EARNINGS***' in line_stripped) and earnings_start == -1):
            earnings_start = i
        elif earnings_start != -1 and ('TAX DEDUCTIONS' in line_stripped or 
                                     ('***' in line_stripped and 'DEDUCTIONS' in line_stripped) or
                                     ('•••' in line_stripped and 'DEDUCTIONS' in line_stripped)):
            earnings_end = i
            break
    
    if earnings_start == -1:
        return []
    
    if earnings_end == -1:
        earnings_end = len(lines)
    
    # Pattern for pdfplumber earnings lines: "Category Hours Amount YTD"
    # Category can have spaces, periods, hyphens, and can start with numbers (e.g., "2/700", "8/900")
    # Numbers can have commas and are decimal format (including hours field)
    earnings_pattern = r'^([A-Za-z0-9][A-Za-z\s\-/\.()&0-9]+?)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)$'
    
    # Extract earnings data from the section
    for i in range(earnings_start + 1, earnings_end):
        line = lines[i].strip()
        
        # Skip empty lines and section headers (be more specific about asterisk patterns)
        if not line or line.startswith('•••') or line.startswith('***') or line.endswith('•••') or line.endswith('***'):
            continue
        
        # Try to match the earnings pattern
        match = re.match(earnings_pattern, line)
        if match:
            category = match.group(1).strip()
            hours = match.group(2).replace(',', '')
            amount = match.group(3).replace(',', '')
            ytd = match.group(4).replace(',', '')
            
            earnings.append({
                'category': category,
                'hours': hours,
                'amount': amount,
                'ytd': ytd
            })
    
    return earnings
