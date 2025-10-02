"""
Centralized regex patterns for deductions data extraction from paystub PDFs.

This module contains all deductions-related regex patterns and extraction logic
used across the paystub processing scripts, eliminating redundancy and improving maintainability.

Handles both TAX DEDUCTIONS and DEDUCTIONS sections.
"""

import re
from typing import Dict, List, Tuple, Optional, Any


class DeductionsRegexPatterns:
    """Centralized container for all deductions-related regex patterns."""
    
    # Section boundary patterns
    TAX_DEDUCTIONS_SECTION_START = r'•••\s*TAX\s+DEDUCTIONS\s*•••|TAX DEDUCTIONS'
    TAX_DEDUCTIONS_SECTION_END = r'•••\s*DEDUCTIONS\s*\*+|(?<!TAX\s)DEDUCTIONS'
    
    DEDUCTIONS_SECTION_START = r'•••\s*DEDUCTIONS\s*\*+|(?<!TAX\s)DEDUCTIONS'
    DEDUCTIONS_SECTION_END = r'•••\s*DIRECT\s+DEPOSITS\s*•••|DIRECT DEPOSITS'
    
    # Alternative section patterns (without bullet decorations)
    SIMPLE_TAX_DEDUCTIONS_START = r'^TAX DEDUCTIONS$'
    SIMPLE_DEDUCTIONS_START = r'^DEDUCTIONS$'
    
    # Data extraction patterns
    CURRENCY_AMOUNT = r'\d+(?:,\d{3})*\.?\d*'
    
    # Line item patterns (for structured extraction)
    LINE_ITEM_WITH_AMOUNTS = r'^([A-Za-z][A-Za-z\s\-/\.()&]+?)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)\s+(\d+\.\d+|\d{1,3}(?:,\d{3})*\.\d+)$'
    
    # Summary patterns
    TOTAL_DEDUCTIONS = r'Total\s+Deductions:\s*([\d,]+\.\d+)'
    
    # Category name patterns (to filter out non-category lines)
    VALID_CATEGORY = r'^[A-Za-z][A-Za-z\s\-/\.()&]+$'
    
    # Non-category patterns (items to skip/filter out)
    NON_CATEGORY_PATTERNS = [
        r'^\*+$',                    # Lines with only asterisks
        r'^•+$',                     # Lines with only bullets
        r'^\s*$',                    # Empty lines
        r'Amount|YTD',               # Header lines
        r'Check\s+Amount',           # Check amount lines
        r'Total\s+Direct',           # Total direct deposits
        r'Total\s+Deductions',       # Total deductions summary
        r'Available\s+PTO',          # PTO balance lines
        r'YTD\s+Paid\s+PTO',        # YTD PTO lines
        r'Period\s+Accrued',         # Period accrued lines
        r'YTD\s+Accrued',           # YTD accrued lines
        r'Gross\s+Earnings',         # Earnings summary
        r'Net\s+Earnings',          # Earnings summary
        r'^\d+\.\d{2}$',            # Pure decimal numbers
        r'^\d+$',                   # Pure integers
        # Bank/Financial institution patterns
        r'Chime',
        r'Green\s+State',
        r'Marine\s+Credit',
        r'Premier\s+Credit',
        r'Stride\s+Bank',
        r'Veridian\s+Credit',
        r'Wells\s+Fargo',
        r'First\s+Interstate',
        r'Earlham\s+Savings'
    ]


class DeductionsDataExtractor:
    """Handles deductions data extraction using centralized patterns."""
    
    def __init__(self):
        self.patterns = DeductionsRegexPatterns()
    
    def find_tax_deductions_section(self, lines: List[str]) -> Tuple[int, int]:
        """
        Find the start and end indices of the TAX DEDUCTIONS section.
        
        Args:
            lines: List of text lines from the paystub
            
        Returns:
            Tuple of (start_idx, end_idx) where -1 indicates not found
        """
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if re.search(self.patterns.TAX_DEDUCTIONS_SECTION_START, line, re.IGNORECASE) and start_idx == -1:
                start_idx = i
            elif start_idx != -1 and re.search(self.patterns.TAX_DEDUCTIONS_SECTION_END, line, re.IGNORECASE):
                # Make sure we don't end on "TAX DEDUCTIONS" header when in TAX section
                if 'TAX' in line:
                    continue
                end_idx = i
                break
        
        if start_idx != -1 and end_idx == -1:
            end_idx = len(lines)
            
        return start_idx, end_idx
    
    def find_deductions_section(self, lines: List[str]) -> Tuple[int, int]:
        """
        Find the start and end indices of the DEDUCTIONS section.
        
        Args:
            lines: List of text lines from the paystub
            
        Returns:
            Tuple of (start_idx, end_idx) where -1 indicates not found
        """
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if re.search(self.patterns.DEDUCTIONS_SECTION_START, line, re.IGNORECASE) and start_idx == -1:
                # Skip "TAX DEDUCTIONS" when looking for "DEDUCTIONS"
                if 'TAX' in line:
                    continue
                start_idx = i
            elif start_idx != -1 and re.search(self.patterns.DEDUCTIONS_SECTION_END, line, re.IGNORECASE):
                end_idx = i
                break
        
        if start_idx != -1 and end_idx == -1:
            end_idx = len(lines)
            
        return start_idx, end_idx
    
    def extract_deduction_categories(self, lines: List[str], start_idx: int, end_idx: int) -> List[str]:
        """
        Extract deduction category names from a deduction section.
        
        Args:
            lines: List of text lines from the paystub
            start_idx: Start index of deduction section
            end_idx: End index of deduction section
            
        Returns:
            List of category names
        """
        categories = []
        
        for i in range(start_idx + 1, end_idx):
            line = lines[i].strip()
            
            # Skip empty lines and lines with special characters
            if not line or any(char in line for char in ['•', '�', '*']):
                continue
            
            # Check against non-category patterns
            is_valid_category = True
            for pattern in self.patterns.NON_CATEGORY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    is_valid_category = False
                    break
            
            # Check if line looks like a valid category name
            if is_valid_category and re.match(self.patterns.VALID_CATEGORY, line):
                categories.append(line)
        
        return categories
    
    def extract_data_values(self, lines: List[str]) -> List[Tuple[str, str]]:
        """
        Extract Amount and YTD pairs from the data section after YTD header.
        
        Args:
            lines: List of text lines from the paystub
            
        Returns:
            List of (amount, ytd) tuples
        """
        data_pairs = []
        ytd_found = False
        
        for line in lines:
            line_clean = line.strip()
            
            # Look for YTD header to start data extraction
            if 'YTD' in line_clean and not ytd_found:
                ytd_found = True
                continue
            
            # Once we find YTD header, extract amount/ytd pairs
            if ytd_found and line_clean:
                # Skip lines that are clearly not data
                if any(char in line_clean for char in ['•', '�', '*']):
                    continue
                
                # Extract two numbers from the line (amount and ytd)
                numbers = re.findall(self.patterns.CURRENCY_AMOUNT, line_clean)
                if len(numbers) >= 2:
                    amount = numbers[0].replace(',', '')
                    ytd = numbers[1].replace(',', '')
                    data_pairs.append((amount, ytd))
                elif len(numbers) == 1:
                    # Single number case - might be amount only
                    amount = numbers[0].replace(',', '')
                    data_pairs.append((amount, '0.00'))
        
        return data_pairs
    
    def extract_structured_line_items(self, lines: List[str], start_idx: int, end_idx: int) -> List[Dict[str, str]]:
        """
        Extract deductions from structured line items (name + amounts on same line).
        
        Args:
            lines: List of text lines from the paystub
            start_idx: Start index of deduction section
            end_idx: End index of deduction section
            
        Returns:
            List of dictionaries with category, amount, ytd
        """
        items = []
        
        for i in range(start_idx + 1, end_idx):
            line = lines[i].strip()
            
            # Try to match the structured line item pattern
            match = re.match(self.patterns.LINE_ITEM_WITH_AMOUNTS, line)
            if match:
                category = match.group(1).strip()
                amount = match.group(2).replace(',', '') if match.group(2) else '0.00'
                ytd = match.group(3).replace(',', '') if match.group(3) else '0.00'
                
                items.append({
                    'category': category,
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
    
    def extract_deductions_data_from_section(self, categories: List[str], data_pairs: List[Tuple[str, str]], start_idx: int = 0) -> List[Dict[str, str]]:
        """
        Combine categories with their corresponding amount/ytd data.
        
        Args:
            categories: List of deduction category names
            data_pairs: List of (amount, ytd) tuples
            start_idx: Starting index in data_pairs for this section
            
        Returns:
            List of deduction records with category, amount, ytd
        """
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


def extract_tax_deductions_data(text: str, page_num: int = 1) -> List[Dict[str, Any]]:
    """
    Main function to extract tax deductions data from paystub text using centralized patterns.
    
    Args:
        text: Full text content of the paystub page
        page_num: Page number for reference
        
    Returns:
        List of tax deduction records with category, amount, ytd
    """
    extractor = DeductionsDataExtractor()
    lines = text.split('\n')
    
    # Find tax deductions section
    start_idx, end_idx = extractor.find_tax_deductions_section(lines)
    if start_idx == -1:
        return []
    
    # Try structured extraction first
    structured_items = extractor.extract_structured_line_items(lines, start_idx, end_idx)
    if structured_items:
        return structured_items
    
    # Fallback to category + data pairs extraction
    categories = extractor.extract_deduction_categories(lines, start_idx, end_idx)
    if not categories:
        return []
    
    data_pairs = extractor.extract_data_values(lines)
    if not data_pairs:
        return []
    
    # Find the data offset for tax deductions (they come after earnings)
    earnings_start, earnings_end = -1, -1
    for i, line in enumerate(lines):
        if 'EARNINGS' in line and earnings_start == -1:
            earnings_start = i
        elif earnings_start != -1 and ('TAX DEDUCTIONS' in line or 'DEDUCTIONS' in line):
            earnings_end = i
            break
    
    # Count earnings categories to determine offset
    earnings_offset = 0
    if earnings_start != -1 and earnings_end != -1:
        for i in range(earnings_start + 1, earnings_end):
            line = lines[i].strip()
            if line and not any(char in line for char in ['•', '�', '*']):
                earnings_offset += 1
    
    return extractor.extract_deductions_data_from_section(categories, data_pairs, earnings_offset)


def extract_deductions_data(text: str, page_num: int = 1) -> List[Dict[str, Any]]:
    """
    Main function to extract regular deductions data from paystub text using centralized patterns.
    
    Args:
        text: Full text content of the paystub page
        page_num: Page number for reference
        
    Returns:
        List of deduction records with category, amount, ytd
    """
    extractor = DeductionsDataExtractor()
    lines = text.split('\n')
    
    # Find deductions section
    start_idx, end_idx = extractor.find_deductions_section(lines)
    if start_idx == -1:
        return []
    
    # Try structured extraction first
    structured_items = extractor.extract_structured_line_items(lines, start_idx, end_idx)
    if structured_items:
        return structured_items
    
    # Fallback to category + data pairs extraction
    categories = extractor.extract_deduction_categories(lines, start_idx, end_idx)
    if not categories:
        return []
    
    data_pairs = extractor.extract_data_values(lines)
    if not data_pairs:
        return []
    
    # Find the data offset for deductions (they come after earnings + tax deductions)
    earnings_offset = 0
    tax_deductions_offset = 0
    
    # Count earnings categories
    earnings_start, earnings_end = -1, -1
    for i, line in enumerate(lines):
        if 'EARNINGS' in line and earnings_start == -1:
            earnings_start = i
        elif earnings_start != -1 and ('TAX DEDUCTIONS' in line or 'DEDUCTIONS' in line):
            earnings_end = i
            break
    
    if earnings_start != -1 and earnings_end != -1:
        for i in range(earnings_start + 1, earnings_end):
            line = lines[i].strip()
            if line and not any(char in line for char in ['•', '�', '*']):
                earnings_offset += 1
    
    # Count tax deductions categories
    tax_start, tax_end = extractor.find_tax_deductions_section(lines)
    if tax_start != -1 and tax_end != -1:
        tax_categories = extractor.extract_deduction_categories(lines, tax_start, tax_end)
        tax_deductions_offset = len(tax_categories)
    
    total_offset = earnings_offset + tax_deductions_offset
    return extractor.extract_deductions_data_from_section(categories, data_pairs, total_offset)


def extract_all_deductions_data(text: str, page_num: int = 1) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract both tax deductions and regular deductions from paystub text.
    
    Args:
        text: Full text content of the paystub page
        page_num: Page number for reference
        
    Returns:
        Tuple of (tax_deductions_list, deductions_list)
    """
    tax_deductions = extract_tax_deductions_data(text, page_num)
    deductions = extract_deductions_data(text, page_num)
    
    return tax_deductions, deductions
