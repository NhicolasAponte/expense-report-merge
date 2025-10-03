"""
Centralized regex patterns for summary data extraction from paystub PDFs.

This module contains all summary-related regex patterns and extraction logic
used for extracting summary financial information from the bottom of paystub pages.

Summary section includes:
- Check Amount, Total Direct Deposit
- Gross Earnings, Total Deductions  
- Net Earnings
- Period Accrued Hours, Available PTO Hours
- YTD Accrued Hours, YTD Paid PTO Hours
"""

import re
from typing import Dict, List, Tuple, Optional, Any


class SummaryRegexPatterns:
    """Centralized container for all summary-related regex patterns."""
    
    # Currency amount pattern (handles negative amounts with trailing minus)
    CURRENCY_AMOUNT = r'\d+(?:,\d{3})*\.?\d*-?'
    
    # Hours pattern (decimal hours)
    HOURS_AMOUNT = r'\d+\.\d{2}'
    
    # Summary section line patterns
    CHECK_AMOUNT_LINE = r'Check\s+Amount:\s*(' + CURRENCY_AMOUNT + r')\s+Total\s+Direct\s+Deposit:\s*(' + CURRENCY_AMOUNT + r')\s+(' + CURRENCY_AMOUNT + r')'
    GROSS_EARNINGS_LINE = r'Gross\s+Earnings:\s*(' + CURRENCY_AMOUNT + r')\s+(' + CURRENCY_AMOUNT + r')\s+Total\s+Deductions:\s*(' + CURRENCY_AMOUNT + r')\s+(' + CURRENCY_AMOUNT + r')'
    NET_EARNINGS_LINE = r'Net\s+Earnings:\s*(' + CURRENCY_AMOUNT + r')'
    PERIOD_PTO_LINE = r'Period\s+Accrued\s+Hours:\s*(' + HOURS_AMOUNT + r')\s+Available\s+PTO\s+Hours:\s*(' + HOURS_AMOUNT + r')'
    YTD_PTO_LINE = r'YTD\s+Accrued\s+Hours:\s*(' + HOURS_AMOUNT + r')\s+YTD\s+Paid\s+PTO\s+Hours:\s*(' + HOURS_AMOUNT + r')'
    
    # Alternative patterns for edge cases
    SIMPLE_CHECK_AMOUNT = r'Check\s+Amount.*?(\d+\.\d{2})'
    SIMPLE_GROSS_EARNINGS = r'Gross\s+Earnings.*?(\d+\.\d{2})'
    SIMPLE_NET_EARNINGS = r'Net\s+Earnings.*?(\d+\.\d{2})'


class SummaryDataExtractor:
    """Handles summary data extraction using centralized patterns."""
    
    def __init__(self):
        self.patterns = SummaryRegexPatterns()
    
    def parse_amount(self, amount_str: str) -> float:
        """
        Parse amount string handling trailing minus signs for negative amounts.
        
        Args:
            amount_str: String representation of amount (e.g., "123.45" or "123.45-")
            
        Returns:
            Float value with proper sign
        """
        if not amount_str:
            return 0.0
        
        clean_amount = amount_str.replace(',', '')
        
        # Handle trailing minus sign (e.g., "352.21-" becomes "-352.21")
        if clean_amount.endswith('-'):
            return -float(clean_amount[:-1])
        else:
            return float(clean_amount)
    
    def extract_summary_data(self, text: str, page_num: int = 1) -> Dict[str, Any]:
        """
        Extract all summary data from paystub text.
        
        Args:
            text: Full text content of the paystub page
            page_num: Page number for reference
            
        Returns:
            Dictionary containing all summary fields
        """
        lines = text.split('\n')
        
        summary_data = {
            'page_number': page_num,
            'check_amount': 0.0,
            'total_direct_deposit_amount': 0.0,
            'total_direct_deposit_ytd': 0.0,
            'gross_earnings_amount': 0.0,
            'gross_earnings_ytd': 0.0,
            'total_deductions_amount': 0.0,
            'total_deductions_ytd': 0.0,
            'net_earnings': 0.0,
            'period_accrued_hours': 0.0,
            'available_pto_hours': 0.0,
            'ytd_accrued_hours': 0.0,
            'ytd_paid_pto_hours': 0.0
        }
        
        for line in lines:
            line = line.strip()
            
            # Extract check amount and total direct deposit
            check_match = re.search(self.patterns.CHECK_AMOUNT_LINE, line, re.IGNORECASE)
            if check_match:
                summary_data['check_amount'] = self.parse_amount(check_match.group(1))
                summary_data['total_direct_deposit_amount'] = self.parse_amount(check_match.group(2))
                summary_data['total_direct_deposit_ytd'] = self.parse_amount(check_match.group(3))
                continue
            
            # Extract gross earnings and total deductions
            gross_match = re.search(self.patterns.GROSS_EARNINGS_LINE, line, re.IGNORECASE)
            if gross_match:
                summary_data['gross_earnings_amount'] = self.parse_amount(gross_match.group(1))
                summary_data['gross_earnings_ytd'] = self.parse_amount(gross_match.group(2))
                summary_data['total_deductions_amount'] = self.parse_amount(gross_match.group(3))
                summary_data['total_deductions_ytd'] = self.parse_amount(gross_match.group(4))
                continue
            
            # Extract net earnings
            net_match = re.search(self.patterns.NET_EARNINGS_LINE, line, re.IGNORECASE)
            if net_match:
                summary_data['net_earnings'] = self.parse_amount(net_match.group(1))
                continue
            
            # Extract period accrued and available PTO hours
            period_pto_match = re.search(self.patterns.PERIOD_PTO_LINE, line, re.IGNORECASE)
            if period_pto_match:
                summary_data['period_accrued_hours'] = float(period_pto_match.group(1))
                summary_data['available_pto_hours'] = float(period_pto_match.group(2))
                continue
            
            # Extract YTD accrued and YTD paid PTO hours
            ytd_pto_match = re.search(self.patterns.YTD_PTO_LINE, line, re.IGNORECASE)
            if ytd_pto_match:
                summary_data['ytd_accrued_hours'] = float(ytd_pto_match.group(1))
                summary_data['ytd_paid_pto_hours'] = float(ytd_pto_match.group(2))
                continue
        
        return summary_data


def extract_summary_data(text: str, page_num: int = 1) -> Dict[str, Any]:
    """
    Main function to extract summary data from paystub text using centralized patterns.
    
    Args:
        text: Full text content of the paystub page
        page_num: Page number for reference
        
    Returns:
        Dictionary containing all summary fields
    """
    extractor = SummaryDataExtractor()
    return extractor.extract_summary_data(text, page_num)
