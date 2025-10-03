#!/usr/bin/env python3
"""
PDF Text Extraction Utilities
Consolidated functionality for extracting text from PDFs using pdfplumber.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pdfplumber
import argparse
from typing import List, Dict, Optional, Tuple
from common_utils import get_pdf_path


class PDFTextExtractor:
    """Utility class for extracting text from PDF files."""
    
    def __init__(self, pdf_path: Optional[str] = None):
        """Initialize with PDF path."""
        self.pdf_path = get_pdf_path(pdf_path)
        self._pdf = None
        self._pages_cache = {}
    
    def __enter__(self):
        """Context manager entry."""
        self._pdf = pdfplumber.open(self.pdf_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._pdf:
            self._pdf.close()
    
    def get_page_count(self) -> int:
        """Get total number of pages in the PDF."""
        if not self._pdf:
            raise RuntimeError("PDF not opened. Use as context manager.")
        return len(self._pdf.pages)
    
    def extract_page_text(self, page_num: int, use_cache: bool = True) -> str:
        """
        Extract text from a specific page.
        
        Args:
            page_num: Page number (1-indexed)
            use_cache: Whether to cache extracted text
            
        Returns:
            Extracted text string
        """
        if not self._pdf:
            raise RuntimeError("PDF not opened. Use as context manager.")
        
        if page_num < 1 or page_num > len(self._pdf.pages):
            raise ValueError(f"Page {page_num} is out of range (1-{len(self._pdf.pages)})")
        
        if use_cache and page_num in self._pages_cache:
            return self._pages_cache[page_num]
        
        page = self._pdf.pages[page_num - 1]  # Convert to 0-indexed
        text = page.extract_text() or ""
        
        if use_cache:
            self._pages_cache[page_num] = text
        
        return text
    
    def extract_page_lines(self, page_num: int, use_cache: bool = True) -> List[str]:
        """
        Extract text lines from a specific page.
        
        Args:
            page_num: Page number (1-indexed)
            use_cache: Whether to cache extracted text
            
        Returns:
            List of text lines
        """
        text = self.extract_page_text(page_num, use_cache)
        return text.split('\n')
    
    def extract_range_text(self, start_page: int, end_page: int) -> Dict[int, str]:
        """
        Extract text from a range of pages.
        
        Args:
            start_page: Starting page number (1-indexed, inclusive)
            end_page: Ending page number (1-indexed, inclusive)
            
        Returns:
            Dictionary mapping page numbers to text content
        """
        if start_page > end_page:
            raise ValueError("Start page must be <= end page")
        
        result = {}
        for page_num in range(start_page, end_page + 1):
            try:
                result[page_num] = self.extract_page_text(page_num)
            except ValueError as e:
                print(f"Warning: {e}")
                continue
        
        return result
    
    def find_section_boundaries(self, page_num: int, 
                              start_patterns: List[str], 
                              end_patterns: List[str]) -> Optional[Tuple[int, int]]:
        """
        Find section boundaries in a page based on patterns.
        
        Args:
            page_num: Page number (1-indexed)
            start_patterns: List of patterns that mark section start
            end_patterns: List of patterns that mark section end
            
        Returns:
            Tuple of (start_line, end_line) indices (0-indexed), or None if not found
        """
        lines = self.extract_page_lines(page_num)
        
        start_line = None
        end_line = None
        
        # Find start pattern
        for i, line in enumerate(lines):
            if any(pattern in line for pattern in start_patterns):
                start_line = i
                break
        
        if start_line is None:
            return None
        
        # Find end pattern after start
        for i, line in enumerate(lines[start_line + 1:], start_line + 1):
            if any(pattern in line for pattern in end_patterns):
                end_line = i
                break
        
        # If no end pattern found, go to end of page
        if end_line is None:
            end_line = len(lines) - 1
        
        return (start_line, end_line)
    
    def extract_section_text(self, page_num: int, 
                           start_patterns: List[str], 
                           end_patterns: List[str]) -> Optional[str]:
        """
        Extract text from a specific section of a page.
        
        Args:
            page_num: Page number (1-indexed)
            start_patterns: List of patterns that mark section start
            end_patterns: List of patterns that mark section end
            
        Returns:
            Section text, or None if section not found
        """
        boundaries = self.find_section_boundaries(page_num, start_patterns, end_patterns)
        if boundaries is None:
            return None
        
        lines = self.extract_page_lines(page_num)
        start_line, end_line = boundaries
        
        return '\n'.join(lines[start_line:end_line + 1])
    
    def search_pages_for_pattern(self, pattern: str, 
                               start_page: int = 1, 
                               end_page: Optional[int] = None) -> List[Tuple[int, List[str]]]:
        """
        Search for a pattern across multiple pages.
        
        Args:
            pattern: Regular expression pattern to search for
            start_page: Starting page number (1-indexed, default 1)
            end_page: Ending page number (1-indexed, default last page)
            
        Returns:
            List of tuples (page_num, matching_lines)
        """
        import re
        
        if end_page is None:
            end_page = self.get_page_count()
        
        results = []
        regex = re.compile(pattern)
        
        for page_num in range(start_page, end_page + 1):
            try:
                lines = self.extract_page_lines(page_num)
                matches = []
                
                for line in lines:
                    if regex.search(line):
                        matches.append(line)
                
                if matches:
                    results.append((page_num, matches))
                    
            except ValueError as e:
                print(f"Warning: {e}")
                continue
        
        return results
    
    def analyze_page_structure(self, page_num: int) -> Dict:
        """
        Analyze the structure of a page.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with page analysis
        """
        lines = self.extract_page_lines(page_num)
        
        analysis = {
            'page_num': page_num,
            'total_lines': len(lines),
            'non_empty_lines': len([l for l in lines if l.strip()]),
            'empty_lines': len([l for l in lines if not l.strip()]),
            'max_line_length': max(len(l) for l in lines) if lines else 0,
            'min_line_length': min(len(l) for l in lines if l.strip()) if any(l.strip() for l in lines) else 0,
            'lines_with_numbers': len([l for l in lines if any(c.isdigit() for c in l)]),
            'lines_with_patterns': {}
        }
        
        # Check for common patterns
        patterns = {
            'earnings_section': [r'•••EARNINGS•••', r'\*\*\*EARNINGS\*\*\*', r'••• EARNINGS •••'],
            'deductions_section': [r'•••DEDUCTIONS•••', r'\*\*\*DEDUCTIONS\*\*\*', r'••• DEDUCTIONS •••'],
            'tax_section': [r'•••TAX DEDUCTIONS•••', r'\*\*\*TAX DEDUCTIONS\*\*\*'],
            'employee_data': [r'^\d{2}-[A-Z]+\d*\s+', r'^[o0]{2}-[A-Z]+\d*\s+'],
            'dates': [r'\d{1,2}/\d{1,2}/\d{4}'],
            'amounts': [r'\d+\.\d{2}']
        }
        
        import re
        for pattern_name, pattern_list in patterns.items():
            matches = []
            for pattern in pattern_list:
                regex = re.compile(pattern)
                for i, line in enumerate(lines):
                    if regex.search(line):
                        matches.append(f"Line {i+1}: {line.strip()}")
            analysis['lines_with_patterns'][pattern_name] = matches
        
        return analysis


def main():
    """Command line interface for PDF text extraction utilities."""
    parser = argparse.ArgumentParser(description='PDF Text Extraction Utilities')
    parser.add_argument('--pdf', help='Path to PDF file (optional, will auto-detect)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract page command
    page_parser = subparsers.add_parser('page', help='Extract text from specific page')
    page_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    page_parser.add_argument('--lines', action='store_true', help='Show line numbers')
    
    # Extract range command
    range_parser = subparsers.add_parser('range', help='Extract text from page range')
    range_parser.add_argument('start_page', type=int, help='Start page (1-indexed)')
    range_parser.add_argument('end_page', type=int, help='End page (1-indexed)')
    
    # Extract section command
    section_parser = subparsers.add_parser('section', help='Extract specific section from page')
    section_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    section_parser.add_argument('--start', nargs='+', required=True, help='Start patterns')
    section_parser.add_argument('--end', nargs='+', required=True, help='End patterns')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for pattern across pages')
    search_parser.add_argument('pattern', help='Regular expression pattern')
    search_parser.add_argument('--start', type=int, default=1, help='Start page')
    search_parser.add_argument('--end', type=int, help='End page')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze page structure')
    analyze_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        with PDFTextExtractor(args.pdf) as extractor:
            if args.command == 'page':
                text = extractor.extract_page_text(args.page_num)
                if args.lines:
                    lines = text.split('\n')
                    for i, line in enumerate(lines, 1):
                        print(f"{i:3}: {line}")
                else:
                    print(text)
            
            elif args.command == 'range':
                texts = extractor.extract_range_text(args.start_page, args.end_page)
                for page_num, text in texts.items():
                    print(f"\n{'='*20} PAGE {page_num} {'='*20}")
                    print(text)
            
            elif args.command == 'section':
                section_text = extractor.extract_section_text(args.page_num, args.start, args.end)
                if section_text:
                    print(section_text)
                else:
                    print(f"Section not found on page {args.page_num}")
            
            elif args.command == 'search':
                results = extractor.search_pages_for_pattern(args.pattern, args.start, args.end)
                for page_num, matches in results:
                    print(f"\nPage {page_num}:")
                    for match in matches:
                        print(f"  {match}")
            
            elif args.command == 'analyze':
                analysis = extractor.analyze_page_structure(args.page_num)
                print(f"Page {analysis['page_num']} Analysis:")
                print(f"  Total lines: {analysis['total_lines']}")
                print(f"  Non-empty lines: {analysis['non_empty_lines']}")
                print(f"  Empty lines: {analysis['empty_lines']}")
                print(f"  Max line length: {analysis['max_line_length']}")
                print(f"  Min line length: {analysis['min_line_length']}")
                print(f"  Lines with numbers: {analysis['lines_with_numbers']}")
                
                print("\nPattern Analysis:")
                for pattern_name, matches in analysis['lines_with_patterns'].items():
                    if matches:
                        print(f"  {pattern_name}: {len(matches)} matches")
                        for match in matches[:3]:  # Show first 3 matches
                            print(f"    {match}")
                        if len(matches) > 3:
                            print(f"    ... and {len(matches) - 3} more")
                    else:
                        print(f"  {pattern_name}: No matches")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())