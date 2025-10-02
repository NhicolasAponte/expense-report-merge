"""
Employee Data Extraction Regex Patterns
Centralized regex patterns for extracting employee information from paystub PDFs.
These patterns support both formatted (newline-separated) and compact layouts.
"""

import re
from typing import Dict, List, Optional

# Name validation suffixes
VALID_NAME_SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}

def is_valid_name(name: str) -> bool:
    """
    Validate if a string looks like a valid employee name.
    
    Args:
        name: The candidate name string to validate
        
    Returns:
        bool: True if the name appears valid, False otherwise
    """
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
    # Remove periods for suffix compare
    if tokens[-1].rstrip('.').upper() in VALID_NAME_SUFFIXES and len(tokens) < 2:
        return False
    # Reasonable total length
    if not (5 < len(name) < 60):
        return False
    return True

class EmployeeRegexPatterns:
    """Container for all employee data extraction regex patterns."""
    
    # ========== EMPLOYEE NAME PATTERNS ==========
    
    # Pattern 1: Formatted layout - name after company address block
    # Anchor: state abbreviation + ZIP then newline then the name line
    # Character class includes letters, period, apostrophe, hyphen, space, comma
    NAME_FORMATTED = r"[A-Z]{2}\s+\d{5}\s*\n([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)(?:,\s*(?:Jr|Sr|II|III|IV|V))?\s*\n"
    
    # Pattern 2: Compact layout - name after date
    # Pattern: Look for name after date - enhanced character class & optional suffix
    NAME_COMPACT = r"\d{1,2}/\d{1,2}/\d{4}\s+([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)(?:,\s*(?:Jr|Sr|II|III|IV|V))?\s*\n"
    
    # Fallback pattern: ZIP code for header identification
    ZIP_CODE = r'\b\d{5}\b'
    
    # ========== PAY RATE PATTERNS ==========
    
    # Pattern 1: Formatted layout - "Pay Rate \n27.50 HW"
    PAY_RATE_FORMATTED = r'Pay Rate\s*\n(\d+\.\d+)\s*HW'
    
    # Pattern 2: Compact layout - "HW 25.00" or "HW25.00"
    PAY_RATE_COMPACT = r'HW\s*(\d+\.\d+)'
    
    # ========== EMPLOYEE NUMBER PATTERNS ==========
    
    # Pattern 1: Formatted layout - "Employee Number \n00-ANA"
    # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
    EMPLOYEE_NUMBER_FORMATTED = r'Employee Number\s*\n([0-9]{2}-[A-Z0-9]{2,4})'
    
    # Pattern 2: Compact layout - "YTD20-XXX" format  
    # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
    EMPLOYEE_NUMBER_COMPACT = r'YTD([0-9]{2}-[A-Z0-9]{2,4})'
    
    # ========== STUB NUMBER PATTERNS ==========
    
    # Pattern 1: Formatted layout - standard newline form
    STUB_NUMBER_FORMATTED = r'Stub Number\s*\n([A-Z0-9]{5,})'
    
    # Pattern 2: Compact layout - inline format
    STUB_NUMBER_COMPACT = r'Stub Number(?:\s|)(D\d{6,})'
    
    # Fallback pattern: any D followed by 6+ digits
    STUB_NUMBER_FALLBACK = r'D\d{6,}'
    
    # ========== PERIOD END DATE PATTERNS ==========
    
    # Pattern 1: Formatted layout - standard newline
    PERIOD_END_FORMATTED = r'Period End\s*\n(\d{1,2}/\d{1,2}/\d{4})'
    
    # Pattern 2: Compact layout - inline before labels
    PERIOD_END_COMPACT = r'(\d{1,2}/\d{1,2}/\d{4}).{0,40}?Period End'
    
    # Merged pattern: "Period End Stub Number" style followed by date + stub
    PERIOD_END_STUB_MERGED = r'(?:Period End\s+Stub Number|Period End Stub Number)?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})'
    
    # General date pattern for fallback
    DATE_GENERAL = r'\b\d{1,2}/\d{1,2}/\d{4}\b'

class EmployeeDataExtractor:
    """Main class for extracting employee data using regex patterns."""
    
    def __init__(self):
        self.patterns = EmployeeRegexPatterns()
    
    def extract_employee_name(self, text: str) -> Optional[str]:
        """
        Extract employee name from text using multiple patterns.
        Auto-detects pdfplumber vs PyPDF2 format.
        
        Args:
            text: The text to search in
            
        Returns:
            str or None: The extracted employee name if found and valid
        """
        lines = text.split('\n')
        
        # pdfplumber format detection: Look for "Name Date" pattern on line 5
        if len(lines) >= 5:
            line5 = lines[4].strip()  # 0-indexed, so line 5 is index 4
            # Pattern: "Name 9/19/2025" format
            pdfplumber_name_pattern = r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+\d{1,2}/\d{1,2}/\d{4}$'
            match = re.match(pdfplumber_name_pattern, line5)
            if match:
                candidate_name = match.group(1).strip()
                if is_valid_name(candidate_name):
                    return candidate_name
        
        # Try formatted layout (PyPDF2 format)
        match = re.search(self.patterns.NAME_FORMATTED, text)
        if match:
            candidate_name = match.group(1).strip()
            if is_valid_name(candidate_name):
                return candidate_name
        
        # Try compact layout (PyPDF2 format)
        match = re.search(self.patterns.NAME_COMPACT, text)
        if match:
            candidate_name = match.group(1).strip()
            if is_valid_name(candidate_name):
                return candidate_name
        
        # Fallback heuristic: scan lines between header and "Employee Number"
        try:
            header_end_idx = 0
            for i, ln in enumerate(lines[:10]):  # search first 10 lines for ZIP
                if re.search(self.patterns.ZIP_CODE, ln):
                    header_end_idx = i
            emp_idx = next((i for i, ln in enumerate(lines) if 'Employee Number' in ln), None)
            window = lines[header_end_idx+1:emp_idx if emp_idx else header_end_idx+6]
            for cand in window:
                c = cand.strip()
                if is_valid_name(c):
                    return c
        except Exception:
            pass
        
        return None
    
    def extract_pay_rate(self, text: str) -> Optional[str]:
        """
        Extract pay rate from text.
        Auto-detects pdfplumber vs PyPDF2 format.
        """
        lines = text.split('\n')
        
        # pdfplumber format detection: Look for data line pattern
        # Pattern: "22-ADJ ···-··-8819 20.50 HW 9/13/2025 D000123144"
        # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
        pdfplumber_data_pattern = r'^[0-9]{2}-[A-Z0-9]{2,4}\s+[·•\-\*\s]+[·•\-\*]*\d+[·•\-\*\s]*(\d+\.\d+)\s+HW\s+\d{1,2}/\d{1,2}/\d{4}\s+D\d{6,}$'
        
        for line in lines:
            line = line.strip()
            match = re.match(pdfplumber_data_pattern, line)
            if match:
                return match.group(1)
        
        # Try formatted layout (PyPDF2 format)
        match = re.search(self.patterns.PAY_RATE_FORMATTED, text)
        if match:
            return match.group(1).strip()
        
        # Try compact layout (PyPDF2 format)
        match = re.search(self.patterns.PAY_RATE_COMPACT, text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_employee_number(self, text: str) -> Optional[str]:
        """
        Extract employee number from text.
        Auto-detects pdfplumber vs PyPDF2 format.
        Format: XX-YYYY where XX=2 digits, YYYY=2-4 alphanumeric characters
        Examples: 00-AN, 10-MC2, 22-MKH1, 20-MKFR
        """
        lines = text.split('\n')
        
        # pdfplumber format detection: Look for data line pattern
        # Pattern: "22-ADJ ···-··-8819 20.50 HW 9/13/2025 D000123144"
        # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
        pdfplumber_data_pattern = r'^([0-9]{2}-[A-Z0-9]{2,4})\s+[·•\-\*\s]+[·•\-\*]*\d+[·•\-\*\s]*\d+\.\d+\s+HW\s+\d{1,2}/\d{1,2}/\d{4}\s+D\d{6,}$'
        
        for line in lines:
            line = line.strip()
            match = re.match(pdfplumber_data_pattern, line)
            if match:
                return match.group(1)
        
        # Try formatted layout (PyPDF2 format)
        match = re.search(self.patterns.EMPLOYEE_NUMBER_FORMATTED, text)
        if match:
            return match.group(1).strip()
        
        # Try compact layout (PyPDF2 format)
        match = re.search(self.patterns.EMPLOYEE_NUMBER_COMPACT, text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_stub_number(self, text: str) -> Optional[str]:
        """
        Extract stub number from text.
        Auto-detects pdfplumber vs PyPDF2 format.
        """
        lines = text.split('\n')
        
        # pdfplumber format detection: Look for data line pattern
        # Pattern: "22-ADJ ···-··-8819 20.50 HW 9/13/2025 D000123144"
        # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
        pdfplumber_data_pattern = r'^[0-9]{2}-[A-Z0-9]{2,4}\s+[·•\-\*\s]+[·•\-\*]*\d+[·•\-\*\s]*\d+\.\d+\s+HW\s+\d{1,2}/\d{1,2}/\d{4}\s+(D\d{6,})$'
        
        for line in lines:
            line = line.strip()
            match = re.match(pdfplumber_data_pattern, line)
            if match:
                return match.group(1)
        
        # Try formatted layout (PyPDF2 format)
        match = re.search(self.patterns.STUB_NUMBER_FORMATTED, text)
        if match:
            candidate = match.group(1).strip()
            if candidate.startswith('D'):
                return candidate
        
        # Try compact layout (PyPDF2 format)
        match = re.search(self.patterns.STUB_NUMBER_COMPACT, text)
        if match:
            return match.group(1).strip()
        
        # Fallback: last D followed by 6+ digits in page
        stub_candidates = re.findall(self.patterns.STUB_NUMBER_FALLBACK, text)
        if stub_candidates:
            return stub_candidates[-1]
        
        return None
    
    def extract_period_end(self, text: str) -> Optional[str]:
        """
        Extract period end date from text.
        Auto-detects pdfplumber vs PyPDF2 format.
        """
        lines = text.split('\n')
        
        # pdfplumber format detection: Look for data line pattern
        # Pattern: "22-ADJ ···-··-8819 20.50 HW 9/13/2025 D000123144"
        # Updated with institutional knowledge: XX-YYYY (2 digits, dash, 2-4 alphanumeric)
        pdfplumber_data_pattern = r'^[0-9]{2}-[A-Z0-9]{2,4}\s+[·•\-\*\s]+[·•\-\*]*\d+[·•\-\*\s]*\d+\.\d+\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+D\d{6,}$'
        
        for line in lines:
            line = line.strip()
            match = re.match(pdfplumber_data_pattern, line)
            if match:
                return match.group(1)
        
        # Try formatted layout (PyPDF2 format)
        match = re.search(self.patterns.PERIOD_END_FORMATTED, text)
        if match:
            return match.group(1).strip()
        
        # Try merged pattern (PyPDF2 format)
        match = re.search(self.patterns.PERIOD_END_STUB_MERGED, text)
        if match:
            return match.group(1)  # Returns the date part
        
        # Try compact layout (PyPDF2 format)
        match = re.search(self.patterns.PERIOD_END_COMPACT, text)
        if match:
            return match.group(1).strip()
        
        # Fallback: choose date closest to 'Pay Rate' or 'Stub Number'
        dates = list(re.finditer(self.patterns.DATE_GENERAL, text))
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
                return best.group(0)
            else:
                # Default: first date (often correct for period end in top block)
                return dates[0].group(0)
        
        return None

# Convenience functions for backward compatibility and easy import
def extract_employee_data_patterns(text: str, page_num: int) -> Dict[str, str]:
    """
    Extract all employee data from text using the centralized patterns.
    
    Args:
        text: The text to extract data from
        page_num: The page number for reference
        
    Returns:
        dict: Dictionary containing extracted employee data
    """
    extractor = EmployeeDataExtractor()
    
    return {
        'page_number': str(page_num),
        'employee_name': extractor.extract_employee_name(text) or '',
        'employee_number': extractor.extract_employee_number(text) or '',
        'pay_rate': extractor.extract_pay_rate(text) or '',
        'stub_number': extractor.extract_stub_number(text) or '',
        'period_end': extractor.extract_period_end(text) or ''
    }

# Export main components for easy importing
__all__ = [
    'EmployeeRegexPatterns',
    'EmployeeDataExtractor', 
    'is_valid_name',
    'extract_employee_data_patterns',
    'VALID_NAME_SUFFIXES'
]