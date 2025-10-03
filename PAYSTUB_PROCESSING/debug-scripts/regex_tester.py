#!/usr/bin/env python3
"""
Regex Testing Framework
Consolidated functionality for testing regex patterns against text data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import re
import argparse
from typing import List, Dict, Optional, Tuple, Any
from pdf_text_utils import PDFTextExtractor
from common_utils import get_pdf_path


class RegexTester:
    """Framework for testing regex patterns against text data."""
    
    def __init__(self):
        """Initialize the regex tester."""
        self.patterns = {}
        self.test_results = {}
    
    def add_pattern(self, name: str, pattern: str, description: str = ""):
        """
        Add a regex pattern to test.
        
        Args:
            name: Pattern name/identifier
            pattern: Regular expression pattern
            description: Optional description of what the pattern matches
        """
        self.patterns[name] = {
            'pattern': pattern,
            'compiled': re.compile(pattern),
            'description': description
        }
    
    def add_standard_patterns(self):
        """Add commonly used patterns from the paystub processing system."""
        patterns = {
            'employee_data_primary': {
                'pattern': r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$',
                'description': 'Primary employee data line pattern'
            },
            'employee_data_fallback': {
                'pattern': r'^([o0]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$',
                'description': 'Fallback employee data pattern for OCR errors'
            },
            'name_date_primary': {
                'pattern': r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$',
                'description': 'Primary employee name and date pattern'
            },
            'name_date_ocr_corrected': {
                'pattern': r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$',
                'description': 'OCR-corrected name pattern (after III/111 and O./0. fixes)'
            },
            'earnings_section_mixed': {
                'pattern': r'(•••EARNINGS•••|••• EARNINGS •••|\*\*\*EARNINGS\*\*\*|\*\*\* EARNINGS \*\*\*)',
                'description': 'Mixed bullet/asterisk earnings section headers'
            },
            'deductions_section_mixed': {
                'pattern': r'(•••DEDUCTIONS•••|••• DEDUCTIONS •••|\*\*\*DEDUCTIONS\*\*\*|\*\*\* DEDUCTIONS \*\*\*)',
                'description': 'Mixed bullet/asterisk deductions section headers'
            },
            'tax_deductions_section_mixed': {
                'pattern': r'(•••TAX DEDUCTIONS•••|••• TAX DEDUCTIONS •••|\*\*\*TAX DEDUCTIONS\*\*\*|\*\*\* TAX DEDUCTIONS \*\*\*)',
                'description': 'Mixed bullet/asterisk tax deductions section headers'
            },
            'earnings_category_numeric': {
                'pattern': r'^\s*([A-Za-z0-9/][A-Za-z0-9/\s\-\.]{0,30}?)\s+(\d+\.\d+)\s*$',
                'description': 'Earnings categories including numeric prefixes (2/700, 8/900)'
            },
            'amount_pattern': {
                'pattern': r'\d+\.\d{2}',
                'description': 'Standard currency amount pattern'
            },
            'date_pattern': {
                'pattern': r'\d{1,2}/\d{1,2}/\d{4}',
                'description': 'Standard date pattern MM/DD/YYYY'
            }
        }
        
        for name, info in patterns.items():
            self.add_pattern(name, info['pattern'], info['description'])
    
    def test_pattern_on_text(self, pattern_name: str, text: str) -> Dict[str, Any]:
        """
        Test a pattern against text.
        
        Args:
            pattern_name: Name of the pattern to test
            text: Text to test against
            
        Returns:
            Dictionary with test results
        """
        if pattern_name not in self.patterns:
            raise ValueError(f"Pattern '{pattern_name}' not found")
        
        pattern_info = self.patterns[pattern_name]
        compiled_pattern = pattern_info['compiled']
        
        lines = text.split('\n')
        matches = []
        
        for i, line in enumerate(lines):
            match = compiled_pattern.search(line)
            if match:
                matches.append({
                    'line_num': i + 1,
                    'line_text': line,
                    'match_text': match.group(0),
                    'groups': match.groups(),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return {
            'pattern_name': pattern_name,
            'pattern': pattern_info['pattern'],
            'description': pattern_info['description'],
            'total_matches': len(matches),
            'matches': matches
        }
    
    def test_pattern_on_page(self, pattern_name: str, page_num: int, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Test a pattern against a specific PDF page.
        
        Args:
            pattern_name: Name of the pattern to test
            page_num: Page number (1-indexed)
            pdf_path: Optional PDF path
            
        Returns:
            Dictionary with test results
        """
        with PDFTextExtractor(pdf_path) as extractor:
            text = extractor.extract_page_text(page_num)
            result = self.test_pattern_on_text(pattern_name, text)
            result['page_num'] = page_num
            result['pdf_path'] = extractor.pdf_path
            return result
    
    def test_multiple_patterns(self, pattern_names: List[str], text: str) -> Dict[str, Dict[str, Any]]:
        """
        Test multiple patterns against the same text.
        
        Args:
            pattern_names: List of pattern names to test
            text: Text to test against
            
        Returns:
            Dictionary mapping pattern names to results
        """
        results = {}
        for pattern_name in pattern_names:
            try:
                results[pattern_name] = self.test_pattern_on_text(pattern_name, text)
            except ValueError as e:
                results[pattern_name] = {'error': str(e)}
        
        return results
    
    def compare_patterns(self, pattern_names: List[str], text: str) -> Dict[str, Any]:
        """
        Compare effectiveness of multiple patterns on the same text.
        
        Args:
            pattern_names: List of pattern names to compare
            text: Text to test against
            
        Returns:
            Comparison results
        """
        results = self.test_multiple_patterns(pattern_names, text)
        
        comparison = {
            'patterns_tested': pattern_names,
            'results': results,
            'summary': {}
        }
        
        for pattern_name, result in results.items():
            if 'error' not in result:
                comparison['summary'][pattern_name] = {
                    'total_matches': result['total_matches'],
                    'description': result['description']
                }
        
        return comparison
    
    def validate_extraction_results(self, pattern_name: str, text: str, expected_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate extraction results against expectations.
        
        Args:
            pattern_name: Name of the pattern to test
            text: Text to test against
            expected_count: Expected number of matches
            
        Returns:
            Validation results
        """
        result = self.test_pattern_on_text(pattern_name, text)
        
        validation = {
            'pattern_name': pattern_name,
            'actual_count': result['total_matches'],
            'expected_count': expected_count,
            'matches': result['matches'],
            'validation_passed': True,
            'issues': []
        }
        
        if expected_count is not None:
            if result['total_matches'] != expected_count:
                validation['validation_passed'] = False
                validation['issues'].append(f"Expected {expected_count} matches, got {result['total_matches']}")
        
        # Additional validations
        for match in result['matches']:
            groups = match['groups']
            
            # Check if groups contain expected data types
            if pattern_name in ['employee_data_primary', 'employee_data_fallback']:
                if len(groups) >= 4:
                    # Check employee ID format
                    emp_id = groups[0]
                    if not re.match(r'[0o]{2}-[A-Z]+[0-9]*', emp_id):
                        validation['issues'].append(f"Invalid employee ID format: {emp_id}")
                    
                    # Check amount format
                    amount = groups[1]
                    if not re.match(r'\d+\.\d+', amount):
                        validation['issues'].append(f"Invalid amount format: {amount}")
                    
                    # Check date format
                    date = groups[2]
                    if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', date):
                        validation['issues'].append(f"Invalid date format: {date}")
            
            elif pattern_name in ['name_date_primary', 'name_date_ocr_corrected']:
                if len(groups) >= 2:
                    # Check name format
                    name = groups[0]
                    if len(name.strip()) < 3:
                        validation['issues'].append(f"Name too short: {name}")
                    
                    # Check date format
                    date = groups[1]
                    if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', date):
                        validation['issues'].append(f"Invalid date format: {date}")
        
        if validation['issues']:
            validation['validation_passed'] = False
        
        return validation
    
    def test_ocr_corrections(self, text: str) -> Dict[str, Any]:
        """
        Test OCR correction effectiveness.
        
        Args:
            text: Text to test (should contain OCR errors)
            
        Returns:
            OCR correction test results
        """
        # Apply OCR corrections
        corrected_text = text
        
        # Common OCR corrections
        ocr_corrections = [
            (r'\b(\w+)\s+111\b', r'\1 III'),  # 111 -> III
            (r'\b(\w+)\s+0\.', r'\1 O.'),     # 0. -> O.
            (r'\boo-', r'00-'),               # oo- -> 00-
        ]
        
        corrections_applied = []
        for pattern, replacement in ocr_corrections:
            matches = re.findall(pattern, corrected_text)
            if matches:
                corrections_applied.extend(matches)
                corrected_text = re.sub(pattern, replacement, corrected_text)
        
        # Test extraction before and after corrections
        before_results = {}
        after_results = {}
        
        test_patterns = ['employee_data_primary', 'employee_data_fallback', 'name_date_primary']
        
        for pattern_name in test_patterns:
            if pattern_name in self.patterns:
                before_results[pattern_name] = self.test_pattern_on_text(pattern_name, text)
                after_results[pattern_name] = self.test_pattern_on_text(pattern_name, corrected_text)
        
        return {
            'original_text': text,
            'corrected_text': corrected_text,
            'corrections_applied': corrections_applied,
            'before_results': before_results,
            'after_results': after_results,
            'improvement_summary': {
                pattern: {
                    'before_matches': before_results[pattern]['total_matches'],
                    'after_matches': after_results[pattern]['total_matches'],
                    'improvement': after_results[pattern]['total_matches'] - before_results[pattern]['total_matches']
                }
                for pattern in before_results.keys()
            }
        }


def main():
    """Command line interface for regex testing."""
    parser = argparse.ArgumentParser(description='Regex Testing Framework')
    parser.add_argument('--pdf', help='Path to PDF file (optional, will auto-detect)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test pattern command
    test_parser = subparsers.add_parser('test', help='Test a pattern')
    test_parser.add_argument('pattern_name', help='Name of pattern to test')
    test_parser.add_argument('--page', type=int, help='Page number to test (1-indexed)')
    test_parser.add_argument('--text', help='Text string to test instead of PDF page')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed match information')
    
    # Compare patterns command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple patterns')
    compare_parser.add_argument('patterns', nargs='+', help='Pattern names to compare')
    compare_parser.add_argument('--page', type=int, help='Page number to test (1-indexed)')
    compare_parser.add_argument('--text', help='Text string to test instead of PDF page')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate extraction results')
    validate_parser.add_argument('pattern_name', help='Name of pattern to validate')
    validate_parser.add_argument('--page', type=int, help='Page number to test (1-indexed)')
    validate_parser.add_argument('--text', help='Text string to test instead of PDF page')
    validate_parser.add_argument('--expected-count', type=int, help='Expected number of matches')
    
    # List patterns command
    list_parser = subparsers.add_parser('list', help='List available patterns')
    
    # OCR test command
    ocr_parser = subparsers.add_parser('ocr', help='Test OCR corrections')
    ocr_parser.add_argument('--page', type=int, help='Page number to test (1-indexed)')
    ocr_parser.add_argument('--text', help='Text string to test instead of PDF page')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tester = RegexTester()
    tester.add_standard_patterns()
    
    try:
        if args.command == 'list':
            print("Available Patterns:")
            print("=" * 50)
            for name, info in tester.patterns.items():
                print(f"{name}:")
                print(f"  Pattern: {info['pattern']}")
                print(f"  Description: {info['description']}")
                print()
        
        elif args.command == 'test':
            # Get text to test
            if hasattr(args, 'text') and args.text:
                text = args.text
            elif hasattr(args, 'page') and args.page:
                with PDFTextExtractor(args.pdf) as extractor:
                    text = extractor.extract_page_text(args.page)
                    print(f"Testing pattern '{args.pattern_name}' on page {args.page}")
            else:
                print("Error: Must specify either --page or --text")
                return 1
            
            result = tester.test_pattern_on_text(args.pattern_name, text)
            
            print(f"Pattern: {result['pattern']}")
            print(f"Description: {result['description']}")
            print(f"Total matches: {result['total_matches']}")
            
            if args.verbose and result['matches']:
                print("\nMatches:")
                for match in result['matches']:
                    print(f"  Line {match['line_num']}: {match['line_text']}")
                    print(f"    Match: {match['match_text']}")
                    if match['groups']:
                        print(f"    Groups: {match['groups']}")
                    print()
        
        elif args.command == 'compare':
            # Get text to test
            if hasattr(args, 'text') and args.text:
                text = args.text
            elif hasattr(args, 'page') and args.page:
                with PDFTextExtractor(args.pdf) as extractor:
                    text = extractor.extract_page_text(args.page)
                    print(f"Comparing patterns on page {args.page}")
            else:
                print("Error: Must specify either --page or --text")
                return 1
            
            comparison = tester.compare_patterns(args.patterns, text)
            
            print("Pattern Comparison Results:")
            print("=" * 50)
            for pattern_name, summary in comparison['summary'].items():
                print(f"{pattern_name}: {summary['total_matches']} matches")
                print(f"  {summary['description']}")
        
        elif args.command == 'validate':
            # Get text to test
            if hasattr(args, 'text') and args.text:
                text = args.text
            elif hasattr(args, 'page') and args.page:
                with PDFTextExtractor(args.pdf) as extractor:
                    text = extractor.extract_page_text(args.page)
                    print(f"Validating pattern '{args.pattern_name}' on page {args.page}")
            else:
                print("Error: Must specify either --page or --text")
                return 1
            
            validation = tester.validate_extraction_results(
                args.pattern_name, 
                text, 
                getattr(args, 'expected_count', None)
            )
            
            print(f"Validation Results for '{validation['pattern_name']}':")
            print(f"  Actual matches: {validation['actual_count']}")
            if validation['expected_count'] is not None:
                print(f"  Expected matches: {validation['expected_count']}")
            print(f"  Validation passed: {validation['validation_passed']}")
            
            if validation['issues']:
                print("  Issues found:")
                for issue in validation['issues']:
                    print(f"    - {issue}")
        
        elif args.command == 'ocr':
            # Get text to test
            if hasattr(args, 'text') and args.text:
                text = args.text
            elif hasattr(args, 'page') and args.page:
                with PDFTextExtractor(args.pdf) as extractor:
                    text = extractor.extract_page_text(args.page)
                    print(f"Testing OCR corrections on page {args.page}")
            else:
                print("Error: Must specify either --page or --text")
                return 1
            
            ocr_results = tester.test_ocr_corrections(text)
            
            print("OCR Correction Test Results:")
            print("=" * 50)
            print(f"Corrections applied: {len(ocr_results['corrections_applied'])}")
            
            print("\nExtraction Improvement Summary:")
            for pattern, improvement in ocr_results['improvement_summary'].items():
                print(f"  {pattern}:")
                print(f"    Before: {improvement['before_matches']} matches")
                print(f"    After: {improvement['after_matches']} matches")
                print(f"    Improvement: +{improvement['improvement']}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())