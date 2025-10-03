#!/usr/bin/env python3
"""
Test the actual pipeline extraction function for page 26.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from regex_patterns.earnings_regex import extract_earnings_data
from common_utils import get_pdf_path
import pdfplumber

def test_pipeline_extraction():
    """Test the actual extraction function used by the pipeline"""
    
    pdf_path = get_pdf_path()
    print(f"Testing pipeline extraction for page 26 with: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[25]  # Page 26 (0-indexed)
        text = page.extract_text()
        
        # Use the same function as the pipeline
        earnings_data = extract_earnings_data(text, page_num=26)
        
        print(f"\nPipeline extraction found {len(earnings_data)} earnings items:")
        for item in earnings_data:
            print(f"  {item['category']}: {item['hours']}h, ${item['amount']}, YTD ${item['ytd']}")
        
        # Expected categories for comparison
        expected_categories = [
            "Holiday", "OT - Loader", "Loaders", "Metal", "Metal-OT", 
            "Paid Time Off", "Paid Time Off Payout", "2/700", "OT 2/700", "8/900", "OT 8/900"
        ]
        actual_categories = [item['category'] for item in earnings_data]
        
        print(f"\nExpected ({len(expected_categories)}): {expected_categories}")
        print(f"Actual ({len(actual_categories)}): {actual_categories}")
        
        missing = set(expected_categories) - set(actual_categories)
        if missing:
            print(f"Still missing: {list(missing)}")
        else:
            print("✅ All categories found!")

if __name__ == "__main__":
    test_pipeline_extraction()