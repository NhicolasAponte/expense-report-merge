#!/usr/bin/env python3
"""
Test the updated name extraction patterns with OCR corrections.
"""

import re

def test_ocr_corrections():
    """Test the OCR corrections for name patterns"""
    
    # Updated patterns from the pipeline
    name_date_pattern = r'^([A-Za-z][A-Za-z\s\.\'\-,]*[A-Za-z](?:\s+(?:III|Jr\.?|Sr\.?))?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
    name_date_fallback_pattern = r'^([A-Za-z][A-Za-z\s\.0-9\'\-,]*[A-Za-z0-9](?:\s+(?:111|Jr\.?|Sr\.?))?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
    
    # Test cases from the problematic pages
    test_cases = [
        # Expected to work with primary pattern
        ("JoelT.Scheuerman 9/19/2025", "JoelT.Scheuerman", True, False),
        ("Dimas T. Rivas 9/19/2025", "Dimas T. Rivas", True, False),
        
        # Expected to need fallback pattern with OCR corrections
        ("Lawrence Porter 111 9/19/2025", "Lawrence Porter III", False, True),
        ("Rex L. Kreie 111 9/19/2025", "Rex L. Kreie III", False, True), 
        ("Christopher 0. Crotchett 9/19/2025", "Christopher O. Crotchett", False, True),
        
        # Additional test cases
        ("John Smith III 9/19/2025", "John Smith III", True, False),
        ("Mary 0. Johnson 111 9/19/2025", "Mary O. Johnson III", False, True),
    ]
    
    print("Testing OCR corrections for name patterns")
    print("=" * 60)
    
    for test_input, expected_name, should_match_primary, should_match_fallback in test_cases:
        print(f"\nTesting: '{test_input}'")
        print(f"Expected: '{expected_name}'")
        
        # Try primary pattern
        match = re.match(name_date_pattern, test_input)
        if match:
            candidate_name = match.group(1).strip()
            if len(candidate_name) >= 3 and ((' ' in candidate_name) or ('.' in candidate_name and len(candidate_name) >= 8)):
                print(f"✓ PRIMARY matched: '{candidate_name}'")
                if candidate_name == expected_name:
                    print("  ✓ Name matches expected")
                else:
                    print(f"  ⚠ Name differs from expected: '{expected_name}'")
                continue
        
        # Try fallback pattern
        fallback_match = re.match(name_date_fallback_pattern, test_input)
        if fallback_match:
            candidate_name = fallback_match.group(1).strip()
            # Apply OCR corrections
            candidate_name = re.sub(r'\b0\.', 'O.', candidate_name)
            candidate_name = re.sub(r'\s111$', ' III', candidate_name)
            
            if len(candidate_name) >= 3 and ((' ' in candidate_name) or ('.' in candidate_name and len(candidate_name) >= 8)):
                print(f"⚠ FALLBACK matched: '{candidate_name}'")
                if candidate_name == expected_name:
                    print("  ✓ Name matches expected after OCR correction")
                else:
                    print(f"  ⚠ Name differs from expected: '{expected_name}'")
                continue
        
        print("✗ No pattern matched")

if __name__ == "__main__":
    test_ocr_corrections()