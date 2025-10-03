#!/usr/bin/env python3
"""
Section Analysis Tool
Consolidated functionality for analyzing specific PDF sections (earnings, deductions, etc.).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import re
import argparse
from typing import List, Dict, Optional, Tuple, Any
from pdf_text_utils import PDFTextExtractor
from common_utils import get_pdf_path


class SectionAnalyzer:
    """Tool for analyzing specific sections within PDF pages."""
    
    def __init__(self, pdf_path: Optional[str] = None):
        """Initialize with PDF path."""
        self.pdf_path = get_pdf_path(pdf_path)
        self.section_patterns = self._load_standard_patterns()
    
    def _load_standard_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load standard section patterns used in paystub processing."""
        return {
            'earnings': {
                'start_patterns': [
                    r'•••EARNINGS•••',
                    r'••• EARNINGS •••',
                    r'\*\*\*EARNINGS\*\*\*',
                    r'\*\*\* EARNINGS \*\*\*'
                ],
                'end_patterns': [
                    r'•••DEDUCTIONS•••',
                    r'••• DEDUCTIONS •••',
                    r'\*\*\*DEDUCTIONS\*\*\*',
                    r'\*\*\* DEDUCTIONS \*\*\*',
                    r'•••TAX DEDUCTIONS•••',
                    r'••• TAX DEDUCTIONS •••',
                    r'\*\*\*TAX DEDUCTIONS\*\*\*',
                    r'\*\*\* TAX DEDUCTIONS \*\*\*'
                ],
                'data_patterns': [
                    r'^\s*([A-Za-z0-9/][A-Za-z0-9/\s\-\.]{0,30}?)\s+(\d+\.\d+)\s*$'
                ],
                'description': 'Earnings section with categories and amounts'
            },
            'deductions': {
                'start_patterns': [
                    r'•••DEDUCTIONS•••',
                    r'••• DEDUCTIONS •••',
                    r'\*\*\*DEDUCTIONS\*\*\*',
                    r'\*\*\* DEDUCTIONS \*\*\*'
                ],
                'end_patterns': [
                    r'•••TAX DEDUCTIONS•••',
                    r'••• TAX DEDUCTIONS •••',
                    r'\*\*\*TAX DEDUCTIONS\*\*\*',
                    r'\*\*\* TAX DEDUCTIONS \*\*\*',
                    r'Page \d+ of \d+'
                ],
                'data_patterns': [
                    r'^\s*([A-Za-z][A-Za-z\s\-\.]{0,30}?)\s+(\d+\.\d+)\s*$'
                ],
                'description': 'Deductions section with categories and amounts'
            },
            'tax_deductions': {
                'start_patterns': [
                    r'•••TAX DEDUCTIONS•••',
                    r'••• TAX DEDUCTIONS •••',
                    r'\*\*\*TAX DEDUCTIONS\*\*\*',
                    r'\*\*\* TAX DEDUCTIONS \*\*\*'
                ],
                'end_patterns': [
                    r'Page \d+ of \d+',
                    r'^\s*$'  # Empty line
                ],
                'data_patterns': [
                    r'^\s*([A-Za-z][A-Za-z\s\-\.]{0,30}?)\s+(\d+\.\d+)\s*$'
                ],
                'description': 'Tax deductions section with categories and amounts'
            },
            'employee_info': {
                'start_patterns': [
                    r'^([0-9o]{2}-[A-Z]+[0-9]*)\s+',
                    r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
                ],
                'end_patterns': [
                    r'•••EARNINGS•••',
                    r'••• EARNINGS •••',
                    r'\*\*\*EARNINGS\*\*\*',
                    r'\*\*\* EARNINGS \*\*\*'
                ],
                'data_patterns': [
                    r'^([0-9o]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$',
                    r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
                ],
                'description': 'Employee information section with ID and name'
            }
        }
    
    def find_section_boundaries(self, page_num: int, section_type: str) -> Optional[Tuple[int, int]]:
        """
        Find section boundaries for a specific section type.
        
        Args:
            page_num: Page number (1-indexed)
            section_type: Type of section ('earnings', 'deductions', 'tax_deductions', 'employee_info')
            
        Returns:
            Tuple of (start_line, end_line) indices (0-indexed), or None if not found
        """
        if section_type not in self.section_patterns:
            raise ValueError(f"Unknown section type: {section_type}")
        
        with PDFTextExtractor(self.pdf_path) as extractor:
            patterns = self.section_patterns[section_type]
            return extractor.find_section_boundaries(
                page_num,
                patterns['start_patterns'],
                patterns['end_patterns']
            )
    
    def extract_section_text(self, page_num: int, section_type: str) -> Optional[str]:
        """
        Extract text from a specific section.
        
        Args:
            page_num: Page number (1-indexed)
            section_type: Type of section
            
        Returns:
            Section text, or None if section not found
        """
        if section_type not in self.section_patterns:
            raise ValueError(f"Unknown section type: {section_type}")
        
        with PDFTextExtractor(self.pdf_path) as extractor:
            patterns = self.section_patterns[section_type]
            return extractor.extract_section_text(
                page_num,
                patterns['start_patterns'],
                patterns['end_patterns']
            )
    
    def analyze_section_data(self, page_num: int, section_type: str) -> Dict[str, Any]:
        """
        Analyze data within a specific section.
        
        Args:
            page_num: Page number (1-indexed)
            section_type: Type of section
            
        Returns:
            Analysis results
        """
        if section_type not in self.section_patterns:
            raise ValueError(f"Unknown section type: {section_type}")
        
        section_text = self.extract_section_text(page_num, section_type)
        if not section_text:
            return {
                'section_type': section_type,
                'page_num': page_num,
                'found': False,
                'error': 'Section not found'
            }
        
        patterns_config = self.section_patterns[section_type]
        lines = section_text.split('\n')
        
        # Find section boundaries within the text
        boundaries = None
        with PDFTextExtractor(self.pdf_path) as extractor:
            boundaries = extractor.find_section_boundaries(
                page_num,
                patterns_config['start_patterns'],
                patterns_config['end_patterns']
            )
        
        # Extract data using patterns
        data_matches = []
        for pattern_str in patterns_config['data_patterns']:
            pattern = re.compile(pattern_str)
            for i, line in enumerate(lines):
                match = pattern.search(line)
                if match:
                    data_matches.append({
                        'line_num': i + 1,
                        'line_text': line.strip(),
                        'match_text': match.group(0),
                        'groups': match.groups(),
                        'pattern_used': pattern_str
                    })
        
        # Section header analysis
        header_line = None
        for i, line in enumerate(lines):
            for start_pattern in patterns_config['start_patterns']:
                if re.search(start_pattern, line):
                    header_line = {
                        'line_num': i + 1,
                        'line_text': line.strip(),
                        'pattern_matched': start_pattern
                    }
                    break
            if header_line:
                break
        
        return {
            'section_type': section_type,
            'page_num': page_num,
            'found': True,
            'description': patterns_config['description'],
            'boundaries': boundaries,
            'total_lines': len(lines),
            'header_line': header_line,
            'data_matches': data_matches,
            'data_count': len(data_matches),
            'raw_text': section_text,
            'lines': lines
        }
    
    def compare_section_patterns(self, page_num: int, section_type: str) -> Dict[str, Any]:
        """
        Compare how different patterns perform on a section.
        
        Args:
            page_num: Page number (1-indexed)
            section_type: Type of section
            
        Returns:
            Pattern comparison results
        """
        section_text = self.extract_section_text(page_num, section_type)
        if not section_text:
            return {
                'section_type': section_type,
                'page_num': page_num,
                'error': 'Section not found'
            }
        
        patterns_config = self.section_patterns[section_type]
        lines = section_text.split('\n')
        
        pattern_results = {}
        
        # Test each data pattern
        for i, pattern_str in enumerate(patterns_config['data_patterns']):
            pattern = re.compile(pattern_str)
            matches = []
            
            for line_num, line in enumerate(lines):
                match = pattern.search(line)
                if match:
                    matches.append({
                        'line_num': line_num + 1,
                        'line_text': line.strip(),
                        'groups': match.groups()
                    })
            
            pattern_results[f'pattern_{i+1}'] = {
                'pattern': pattern_str,
                'matches': matches,
                'match_count': len(matches)
            }
        
        # Find best performing pattern
        best_pattern = None
        max_matches = 0
        for pattern_key, result in pattern_results.items():
            if result['match_count'] > max_matches:
                max_matches = result['match_count']
                best_pattern = pattern_key
        
        return {
            'section_type': section_type,
            'page_num': page_num,
            'pattern_results': pattern_results,
            'best_pattern': best_pattern,
            'max_matches': max_matches,
            'total_lines': len(lines)
        }
    
    def validate_section_extraction(self, page_num: int, section_type: str, 
                                  expected_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate section extraction results.
        
        Args:
            page_num: Page number (1-indexed)
            section_type: Type of section
            expected_count: Expected number of data items
            
        Returns:
            Validation results
        """
        analysis = self.analyze_section_data(page_num, section_type)
        
        if not analysis.get('found', False):
            return {
                'section_type': section_type,
                'page_num': page_num,
                'validation_passed': False,
                'issues': ['Section not found'],
                'analysis': analysis
            }
        
        issues = []
        
        # Check if section header was found
        if not analysis['header_line']:
            issues.append('Section header not detected')
        
        # Check data count
        data_count = analysis['data_count']
        if expected_count is not None:
            if data_count != expected_count:
                issues.append(f'Expected {expected_count} data items, found {data_count}')
        
        # Validate data format
        for match in analysis['data_matches']:
            groups = match['groups']
            
            if section_type in ['earnings', 'deductions', 'tax_deductions']:
                if len(groups) >= 2:
                    category = groups[0]
                    amount = groups[1]
                    
                    # Check category format
                    if not category or len(category.strip()) < 1:
                        issues.append(f'Invalid category: "{category}"')
                    
                    # Check amount format
                    try:
                        float(amount)
                    except ValueError:
                        issues.append(f'Invalid amount format: "{amount}"')
            
            elif section_type == 'employee_info':
                if len(groups) >= 2:
                    # Could be employee ID or name pattern
                    if re.match(r'[0-9o]{2}-[A-Z]+[0-9]*', groups[0]):
                        # Employee ID pattern
                        emp_id = groups[0]
                        if not re.match(r'[0-9o]{2}-[A-Z]+[0-9]*', emp_id):
                            issues.append(f'Invalid employee ID format: "{emp_id}"')
                    else:
                        # Name pattern
                        name = groups[0]
                        date = groups[1]
                        
                        if len(name.strip()) < 3:
                            issues.append(f'Name too short: "{name}"')
                        
                        if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', date):
                            issues.append(f'Invalid date format: "{date}"')
        
        return {
            'section_type': section_type,
            'page_num': page_num,
            'validation_passed': len(issues) == 0,
            'issues': issues,
            'data_count': data_count,
            'expected_count': expected_count,
            'analysis': analysis
        }
    
    def analyze_mixed_patterns(self, page_num: int) -> Dict[str, Any]:
        """
        Analyze if a page uses mixed bullet/asterisk patterns.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Mixed pattern analysis
        """
        with PDFTextExtractor(self.pdf_path) as extractor:
            lines = extractor.extract_page_lines(page_num)
        
        bullet_patterns = []
        asterisk_patterns = []
        
        # Check for different header patterns
        patterns_to_check = {
            'bullet_earnings': r'•••EARNINGS•••|••• EARNINGS •••',
            'asterisk_earnings': r'\*\*\*EARNINGS\*\*\*|\*\*\* EARNINGS \*\*\*',
            'bullet_deductions': r'•••DEDUCTIONS•••|••• DEDUCTIONS •••',
            'asterisk_deductions': r'\*\*\*DEDUCTIONS\*\*\*|\*\*\* DEDUCTIONS \*\*\*',
            'bullet_tax': r'•••TAX DEDUCTIONS•••|••• TAX DEDUCTIONS •••',
            'asterisk_tax': r'\*\*\*TAX DEDUCTIONS\*\*\*|\*\*\* TAX DEDUCTIONS \*\*\*'
        }
        
        pattern_matches = {}
        for pattern_name, pattern_str in patterns_to_check.items():
            matches = []
            for i, line in enumerate(lines):
                if re.search(pattern_str, line):
                    matches.append({
                        'line_num': i + 1,
                        'line_text': line.strip()
                    })
            pattern_matches[pattern_name] = matches
            
            if 'bullet' in pattern_name and matches:
                bullet_patterns.extend(matches)
            elif 'asterisk' in pattern_name and matches:
                asterisk_patterns.extend(matches)
        
        # Determine pattern type
        pattern_type = 'unknown'
        if bullet_patterns and asterisk_patterns:
            pattern_type = 'mixed'
        elif bullet_patterns:
            pattern_type = 'bullet'
        elif asterisk_patterns:
            pattern_type = 'asterisk'
        
        return {
            'page_num': page_num,
            'pattern_type': pattern_type,
            'bullet_patterns': bullet_patterns,
            'asterisk_patterns': asterisk_patterns,
            'pattern_matches': pattern_matches,
            'total_patterns_found': len(bullet_patterns) + len(asterisk_patterns)
        }


def main():
    """Command line interface for section analysis."""
    parser = argparse.ArgumentParser(description='Section Analysis Tool')
    parser.add_argument('--pdf', help='Path to PDF file (optional, will auto-detect)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze section command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a specific section')
    analyze_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    analyze_parser.add_argument('section_type', choices=['earnings', 'deductions', 'tax_deductions', 'employee_info'],
                               help='Type of section to analyze')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    
    # Compare patterns command
    compare_parser = subparsers.add_parser('compare', help='Compare patterns for a section')
    compare_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    compare_parser.add_argument('section_type', choices=['earnings', 'deductions', 'tax_deductions', 'employee_info'],
                               help='Type of section to analyze')
    
    # Validate section command
    validate_parser = subparsers.add_parser('validate', help='Validate section extraction')
    validate_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    validate_parser.add_argument('section_type', choices=['earnings', 'deductions', 'tax_deductions', 'employee_info'],
                                help='Type of section to validate')
    validate_parser.add_argument('--expected-count', type=int, help='Expected number of data items')
    
    # Mixed patterns command
    mixed_parser = subparsers.add_parser('mixed', help='Analyze mixed bullet/asterisk patterns')
    mixed_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    
    # Extract section command
    extract_parser = subparsers.add_parser('extract', help='Extract section text')
    extract_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    extract_parser.add_argument('section_type', choices=['earnings', 'deductions', 'tax_deductions', 'employee_info'],
                               help='Type of section to extract')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    analyzer = SectionAnalyzer(args.pdf)
    
    try:
        if args.command == 'analyze':
            result = analyzer.analyze_section_data(args.page_num, args.section_type)
            
            if result.get('found', False):
                print(f"Section Analysis: {result['section_type']} on page {result['page_num']}")
                print(f"Description: {result['description']}")
                print(f"Total lines: {result['total_lines']}")
                print(f"Data matches: {result['data_count']}")
                
                if result['header_line']:
                    print(f"Header found: {result['header_line']['line_text']}")
                else:
                    print("Header: Not detected")
                
                if args.verbose:
                    print("\nData matches:")
                    for match in result['data_matches']:
                        print(f"  Line {match['line_num']}: {match['line_text']}")
                        print(f"    Groups: {match['groups']}")
                    
                    print(f"\nSection boundaries: {result['boundaries']}")
            else:
                print(f"Section not found: {result.get('error', 'Unknown error')}")
        
        elif args.command == 'compare':
            result = analyzer.compare_section_patterns(args.page_num, args.section_type)
            
            if 'error' not in result:
                print(f"Pattern Comparison: {result['section_type']} on page {result['page_num']}")
                print(f"Best pattern: {result['best_pattern']} ({result['max_matches']} matches)")
                
                for pattern_key, pattern_result in result['pattern_results'].items():
                    print(f"\n{pattern_key}: {pattern_result['match_count']} matches")
                    print(f"  Pattern: {pattern_result['pattern']}")
            else:
                print(f"Error: {result['error']}")
        
        elif args.command == 'validate':
            result = analyzer.validate_section_extraction(
                args.page_num, 
                args.section_type, 
                getattr(args, 'expected_count', None)
            )
            
            print(f"Validation: {result['section_type']} on page {result['page_num']}")
            print(f"Passed: {result['validation_passed']}")
            print(f"Data count: {result['data_count']}")
            if result['expected_count'] is not None:
                print(f"Expected count: {result['expected_count']}")
            
            if result['issues']:
                print("Issues:")
                for issue in result['issues']:
                    print(f"  - {issue}")
        
        elif args.command == 'mixed':
            result = analyzer.analyze_mixed_patterns(args.page_num)
            
            print(f"Mixed Pattern Analysis: Page {result['page_num']}")
            print(f"Pattern type: {result['pattern_type']}")
            print(f"Total patterns found: {result['total_patterns_found']}")
            
            if result['bullet_patterns']:
                print(f"\nBullet patterns ({len(result['bullet_patterns'])}):")
                for pattern in result['bullet_patterns']:
                    print(f"  Line {pattern['line_num']}: {pattern['line_text']}")
            
            if result['asterisk_patterns']:
                print(f"\nAsterisk patterns ({len(result['asterisk_patterns'])}):")
                for pattern in result['asterisk_patterns']:
                    print(f"  Line {pattern['line_num']}: {pattern['line_text']}")
        
        elif args.command == 'extract':
            text = analyzer.extract_section_text(args.page_num, args.section_type)
            
            if text:
                print(f"Section Text: {args.section_type} on page {args.page_num}")
                print("=" * 50)
                print(text)
            else:
                print(f"Section {args.section_type} not found on page {args.page_num}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())