#!/usr/bin/env python3
"""
Page Analysis Tool
Consolidated functionality for analyzing specific problematic pages with configurable patterns.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import re
import argparse
import json
from typing import List, Dict, Optional, Tuple, Any
from pdf_text_utils import PDFTextExtractor
from regex_tester import RegexTester
from section_analyzer import SectionAnalyzer
from common_utils import get_pdf_path


class PageAnalyzer:
    """Tool for comprehensive analysis of specific PDF pages."""
    
    def __init__(self, pdf_path: Optional[str] = None):
        """Initialize with PDF path."""
        self.pdf_path = get_pdf_path(pdf_path)
        self.regex_tester = RegexTester()
        self.regex_tester.add_standard_patterns()
        self.section_analyzer = SectionAnalyzer(pdf_path)
    
    def analyze_page_comprehensive(self, page_num: int) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a page.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Comprehensive analysis results
        """
        with PDFTextExtractor(self.pdf_path) as extractor:
            # Basic page structure
            structure = extractor.analyze_page_structure(page_num)
            
            # Section analysis
            sections = {}
            for section_type in ['earnings', 'deductions', 'tax_deductions', 'employee_info']:
                try:
                    sections[section_type] = self.section_analyzer.analyze_section_data(page_num, section_type)
                except Exception as e:
                    sections[section_type] = {'error': str(e)}
            
            # Pattern analysis
            text = extractor.extract_page_text(page_num)
            pattern_results = {}
            
            # Test key patterns
            key_patterns = ['employee_data_primary', 'employee_data_fallback', 'name_date_primary']
            for pattern_name in key_patterns:
                try:
                    pattern_results[pattern_name] = self.regex_tester.test_pattern_on_text(pattern_name, text)
                except Exception as e:
                    pattern_results[pattern_name] = {'error': str(e)}
            
            # Mixed pattern analysis
            mixed_analysis = self.section_analyzer.analyze_mixed_patterns(page_num)
            
            # OCR correction analysis
            ocr_analysis = self.regex_tester.test_ocr_corrections(text)
            
            return {
                'page_num': page_num,
                'pdf_path': self.pdf_path,
                'structure': structure,
                'sections': sections,
                'patterns': pattern_results,
                'mixed_patterns': mixed_analysis,
                'ocr_corrections': ocr_analysis,
                'summary': self._generate_page_summary(structure, sections, pattern_results, mixed_analysis)
            }
    
    def _generate_page_summary(self, structure: Dict, sections: Dict, 
                             patterns: Dict, mixed_analysis: Dict) -> Dict[str, Any]:
        """Generate a summary of page analysis."""
        summary = {
            'total_lines': structure.get('total_lines', 0),
            'non_empty_lines': structure.get('non_empty_lines', 0),
            'sections_found': [],
            'sections_missing': [],
            'pattern_matches': {},
            'pattern_type': mixed_analysis.get('pattern_type', 'unknown'),
            'issues': []
        }
        
        # Check sections
        for section_type, section_data in sections.items():
            if section_data.get('found', False):
                summary['sections_found'].append(section_type)
            else:
                summary['sections_missing'].append(section_type)
        
        # Check patterns
        for pattern_name, pattern_data in patterns.items():
            if 'error' not in pattern_data:
                summary['pattern_matches'][pattern_name] = pattern_data.get('total_matches', 0)
        
        # Identify potential issues
        if not summary['sections_found']:
            summary['issues'].append('No sections detected')
        
        if all(count == 0 for count in summary['pattern_matches'].values()):
            summary['issues'].append('No pattern matches found')
        
        if summary['pattern_type'] == 'mixed':
            summary['issues'].append('Mixed bullet/asterisk patterns detected')
        
        return summary
    
    def analyze_problematic_pages(self, page_numbers: List[int]) -> Dict[str, Any]:
        """
        Analyze multiple problematic pages.
        
        Args:
            page_numbers: List of page numbers to analyze
            
        Returns:
            Analysis results for all pages
        """
        results = {}
        
        for page_num in page_numbers:
            try:
                results[page_num] = self.analyze_page_comprehensive(page_num)
            except Exception as e:
                results[page_num] = {
                    'page_num': page_num,
                    'error': str(e)
                }
        
        # Generate cross-page analysis
        cross_analysis = self._analyze_cross_page_patterns(results)
        
        return {
            'pages_analyzed': page_numbers,
            'individual_results': results,
            'cross_analysis': cross_analysis
        }
    
    def _analyze_cross_page_patterns(self, page_results: Dict[int, Dict]) -> Dict[str, Any]:
        """Analyze patterns across multiple pages."""
        cross_analysis = {
            'common_issues': {},
            'pattern_consistency': {},
            'section_availability': {},
            'pattern_type_distribution': {}
        }
        
        # Count common issues
        issue_counts = {}
        pattern_type_counts = {}
        section_counts = {}
        
        for page_num, result in page_results.items():
            if 'error' in result:
                continue
            
            summary = result.get('summary', {})
            
            # Count issues
            for issue in summary.get('issues', []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            # Count pattern types
            pattern_type = summary.get('pattern_type', 'unknown')
            pattern_type_counts[pattern_type] = pattern_type_counts.get(pattern_type, 0) + 1
            
            # Count section availability
            for section in summary.get('sections_found', []):
                section_counts[section] = section_counts.get(section, 0) + 1
        
        cross_analysis['common_issues'] = issue_counts
        cross_analysis['pattern_type_distribution'] = pattern_type_counts
        cross_analysis['section_availability'] = section_counts
        
        return cross_analysis
    
    def compare_with_working_page(self, problematic_page: int, working_page: int) -> Dict[str, Any]:
        """
        Compare a problematic page with a working page.
        
        Args:
            problematic_page: Page number that has issues
            working_page: Page number that works correctly
            
        Returns:
            Comparison results
        """
        problematic_analysis = self.analyze_page_comprehensive(problematic_page)
        working_analysis = self.analyze_page_comprehensive(working_page)
        
        comparison = {
            'problematic_page': problematic_page,
            'working_page': working_page,
            'differences': {},
            'similarities': {},
            'recommendations': []
        }
        
        # Compare summaries
        prob_summary = problematic_analysis.get('summary', {})
        work_summary = working_analysis.get('summary', {})
        
        # Pattern type differences
        if prob_summary.get('pattern_type') != work_summary.get('pattern_type'):
            comparison['differences']['pattern_type'] = {
                'problematic': prob_summary.get('pattern_type'),
                'working': work_summary.get('pattern_type')
            }
            comparison['recommendations'].append(
                f"Consider using {work_summary.get('pattern_type')} pattern format"
            )
        
        # Section differences
        prob_sections = set(prob_summary.get('sections_found', []))
        work_sections = set(work_summary.get('sections_found', []))
        
        missing_sections = work_sections - prob_sections
        if missing_sections:
            comparison['differences']['missing_sections'] = list(missing_sections)
            comparison['recommendations'].append(
                f"Check section detection for: {', '.join(missing_sections)}"
            )
        
        # Pattern match differences
        prob_matches = prob_summary.get('pattern_matches', {})
        work_matches = work_summary.get('pattern_matches', {})
        
        for pattern_name in set(prob_matches.keys()) | set(work_matches.keys()):
            prob_count = prob_matches.get(pattern_name, 0)
            work_count = work_matches.get(pattern_name, 0)
            
            if prob_count != work_count:
                comparison['differences'][f'pattern_{pattern_name}'] = {
                    'problematic': prob_count,
                    'working': work_count
                }
                
                if prob_count == 0 and work_count > 0:
                    comparison['recommendations'].append(
                        f"Pattern {pattern_name} not matching - check text formatting"
                    )
        
        return comparison
    
    def analyze_employee_extraction_issues(self, page_num: int) -> Dict[str, Any]:
        """
        Specifically analyze employee data extraction issues.
        
        Args:
            page_num: Page number to analyze
            
        Returns:
            Employee extraction analysis
        """
        with PDFTextExtractor(self.pdf_path) as extractor:
            text = extractor.extract_page_text(page_num)
            lines = text.split('\n')
        
        analysis = {
            'page_num': page_num,
            'employee_patterns': {},
            'potential_employee_lines': [],
            'ocr_issues': [],
            'recommendations': []
        }
        
        # Test various employee patterns
        employee_patterns = {
            'primary_data': r'^([0-9]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$',
            'fallback_data': r'^([o0]{2}-[A-Z]+[0-9]*)\s+[·•\*\-\s]+[0-9\*\-•·]+\s+(\d+\.\d+)\s+HW\s+(\d{1,2}/\d{1,2}/\d{4})\s+(D\d{6,})$',
            'primary_name': r'^([A-Za-z][A-Za-z\.\'\- ,]{3,60}?)\s+(\d{1,2}/\d{1,2}/\d{4})$',
            'loose_employee_id': r'^([0-9o]{2}-[A-Z]+[0-9]*)',
            'loose_name': r'^([A-Za-z][A-Za-z\.\'\- ,]{3,30})',
            'date_pattern': r'(\d{1,2}/\d{1,2}/\d{4})',
            'amount_pattern': r'(\d+\.\d{2})'
        }
        
        for pattern_name, pattern_str in employee_patterns.items():
            pattern = re.compile(pattern_str)
            matches = []
            
            for i, line in enumerate(lines):
                match = pattern.search(line)
                if match:
                    matches.append({
                        'line_num': i + 1,
                        'line_text': line.strip(),
                        'groups': match.groups()
                    })
            
            analysis['employee_patterns'][pattern_name] = {
                'pattern': pattern_str,
                'matches': matches,
                'count': len(matches)
            }
        
        # Look for potential employee lines that don't match patterns
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if line contains employee-like data
            has_employee_id = bool(re.search(r'[0-9o]{2}-[A-Z]+', line_clean))
            has_amount = bool(re.search(r'\d+\.\d{2}', line_clean))
            has_date = bool(re.search(r'\d{1,2}/\d{1,2}/\d{4}', line_clean))
            has_name_like = bool(re.search(r'^[A-Za-z][A-Za-z\.\'\- ,]{5,}', line_clean))
            
            # If it looks employee-related but doesn't match main patterns
            if (has_employee_id or has_amount or has_name_like) and has_date:
                matched_main_pattern = False
                for pattern_name in ['primary_data', 'fallback_data', 'primary_name']:
                    if analysis['employee_patterns'][pattern_name]['matches']:
                        for match in analysis['employee_patterns'][pattern_name]['matches']:
                            if match['line_num'] == i + 1:
                                matched_main_pattern = True
                                break
                    if matched_main_pattern:
                        break
                
                if not matched_main_pattern:
                    analysis['potential_employee_lines'].append({
                        'line_num': i + 1,
                        'line_text': line_clean,
                        'has_employee_id': has_employee_id,
                        'has_amount': has_amount,
                        'has_date': has_date,
                        'has_name_like': has_name_like
                    })
        
        # Check for common OCR issues
        ocr_patterns = [
            (r'111\b', 'III', '111 should be III'),
            (r'\b0\.', 'O.', '0. should be O.'),
            (r'\boo-', '00-', 'oo- should be 00-'),
            (r'\b0o-', '00-', '0o- should be 00-'),
            (r'\bo0-', '00-', 'o0- should be 00-')
        ]
        
        for pattern, replacement, description in ocr_patterns:
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    analysis['ocr_issues'].append({
                        'line_num': i + 1,
                        'line_text': line.strip(),
                        'issue': description,
                        'pattern': pattern,
                        'suggested_fix': replacement
                    })
        
        # Generate recommendations
        if analysis['employee_patterns']['primary_data']['count'] == 0:
            if analysis['employee_patterns']['fallback_data']['count'] > 0:
                analysis['recommendations'].append("Primary pattern failed but fallback worked - OCR issues likely")
            else:
                analysis['recommendations'].append("No employee data patterns matched - check text formatting")
        
        if analysis['employee_patterns']['primary_name']['count'] == 0:
            analysis['recommendations'].append("No employee names extracted - check name pattern")
        
        if analysis['ocr_issues']:
            analysis['recommendations'].append(f"Found {len(analysis['ocr_issues'])} potential OCR issues")
        
        if analysis['potential_employee_lines']:
            analysis['recommendations'].append(f"Found {len(analysis['potential_employee_lines'])} lines that look employee-related but don't match patterns")
        
        return analysis
    
    def save_analysis_report(self, analysis_result: Dict[str, Any], 
                           output_file: str, format_type: str = 'json') -> None:
        """
        Save analysis results to file.
        
        Args:
            analysis_result: Analysis results to save
            output_file: Output file path
            format_type: Format type ('json' or 'text')
        """
        if format_type == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, default=str)
        elif format_type == 'text':
            with open(output_file, 'w', encoding='utf-8') as f:
                self._write_text_report(analysis_result, f)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    
    def _write_text_report(self, analysis_result: Dict[str, Any], file_handle) -> None:
        """Write analysis results as text report."""
        if 'page_num' in analysis_result:
            # Single page analysis
            self._write_single_page_report(analysis_result, file_handle)
        elif 'pages_analyzed' in analysis_result:
            # Multiple pages analysis
            self._write_multi_page_report(analysis_result, file_handle)
        else:
            # Unknown format
            file_handle.write("ANALYSIS REPORT\n")
            file_handle.write("=" * 50 + "\n")
            file_handle.write(json.dumps(analysis_result, indent=2, default=str))
    
    def _write_single_page_report(self, result: Dict[str, Any], file_handle) -> None:
        """Write single page analysis report."""
        file_handle.write(f"PAGE ANALYSIS REPORT\n")
        file_handle.write("=" * 50 + "\n")
        file_handle.write(f"Page: {result['page_num']}\n")
        file_handle.write(f"PDF: {result['pdf_path']}\n\n")
        
        # Summary
        summary = result.get('summary', {})
        file_handle.write("SUMMARY\n")
        file_handle.write("-" * 20 + "\n")
        file_handle.write(f"Total lines: {summary.get('total_lines', 0)}\n")
        file_handle.write(f"Non-empty lines: {summary.get('non_empty_lines', 0)}\n")
        file_handle.write(f"Sections found: {', '.join(summary.get('sections_found', []))}\n")
        file_handle.write(f"Pattern type: {summary.get('pattern_type', 'unknown')}\n")
        
        if summary.get('issues'):
            file_handle.write(f"Issues: {'; '.join(summary['issues'])}\n")
        
        file_handle.write("\n")
        
        # Pattern matches
        file_handle.write("PATTERN MATCHES\n")
        file_handle.write("-" * 20 + "\n")
        for pattern_name, count in summary.get('pattern_matches', {}).items():
            file_handle.write(f"{pattern_name}: {count} matches\n")
        
        file_handle.write("\n")
    
    def _write_multi_page_report(self, result: Dict[str, Any], file_handle) -> None:
        """Write multiple pages analysis report."""
        file_handle.write(f"MULTI-PAGE ANALYSIS REPORT\n")
        file_handle.write("=" * 50 + "\n")
        file_handle.write(f"Pages analyzed: {result['pages_analyzed']}\n\n")
        
        # Cross-page analysis
        cross = result.get('cross_analysis', {})
        file_handle.write("CROSS-PAGE ANALYSIS\n")
        file_handle.write("-" * 30 + "\n")
        
        if cross.get('common_issues'):
            file_handle.write("Common issues:\n")
            for issue, count in cross['common_issues'].items():
                file_handle.write(f"  {issue}: {count} pages\n")
        
        if cross.get('pattern_type_distribution'):
            file_handle.write("\nPattern type distribution:\n")
            for pattern_type, count in cross['pattern_type_distribution'].items():
                file_handle.write(f"  {pattern_type}: {count} pages\n")
        
        file_handle.write("\n")
        
        # Individual page summaries
        file_handle.write("INDIVIDUAL PAGE SUMMARIES\n")
        file_handle.write("-" * 30 + "\n")
        for page_num, page_result in result.get('individual_results', {}).items():
            if 'error' in page_result:
                file_handle.write(f"Page {page_num}: ERROR - {page_result['error']}\n")
            else:
                summary = page_result.get('summary', {})
                file_handle.write(f"Page {page_num}: {len(summary.get('sections_found', []))} sections, ")
                file_handle.write(f"{sum(summary.get('pattern_matches', {}).values())} pattern matches")
                if summary.get('issues'):
                    file_handle.write(f" - Issues: {'; '.join(summary['issues'])}")
                file_handle.write("\n")


def main():
    """Command line interface for page analysis."""
    parser = argparse.ArgumentParser(description='Page Analysis Tool')
    parser.add_argument('--pdf', help='Path to PDF file (optional, will auto-detect)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze single page
    single_parser = subparsers.add_parser('page', help='Analyze a single page')
    single_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    single_parser.add_argument('--output', help='Save report to file')
    single_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    # Analyze multiple pages
    multi_parser = subparsers.add_parser('pages', help='Analyze multiple pages')
    multi_parser.add_argument('page_numbers', nargs='+', type=int, help='Page numbers (1-indexed)')
    multi_parser.add_argument('--output', help='Save report to file')
    multi_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    # Compare pages
    compare_parser = subparsers.add_parser('compare', help='Compare problematic page with working page')
    compare_parser.add_argument('problematic_page', type=int, help='Problematic page number')
    compare_parser.add_argument('working_page', type=int, help='Working page number')
    
    # Analyze employee extraction
    employee_parser = subparsers.add_parser('employee', help='Analyze employee extraction issues')
    employee_parser.add_argument('page_num', type=int, help='Page number (1-indexed)')
    employee_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    analyzer = PageAnalyzer(args.pdf)
    
    try:
        if args.command == 'page':
            result = analyzer.analyze_page_comprehensive(args.page_num)
            
            # Print summary
            summary = result['summary']
            print(f"Page {args.page_num} Analysis:")
            print(f"  Lines: {summary['total_lines']} total, {summary['non_empty_lines']} non-empty")
            print(f"  Sections: {', '.join(summary['sections_found']) if summary['sections_found'] else 'None'}")
            print(f"  Pattern type: {summary['pattern_type']}")
            print(f"  Pattern matches: {sum(summary['pattern_matches'].values())}")
            
            if summary['issues']:
                print(f"  Issues: {'; '.join(summary['issues'])}")
            
            if hasattr(args, 'output') and args.output:
                analyzer.save_analysis_report(result, args.output, args.format)
                print(f"\nDetailed report saved to: {args.output}")
        
        elif args.command == 'pages':
            result = analyzer.analyze_problematic_pages(args.page_numbers)
            
            print(f"Multi-page Analysis: {len(args.page_numbers)} pages")
            
            # Print cross-analysis
            cross = result['cross_analysis']
            if cross['common_issues']:
                print("Common issues:")
                for issue, count in cross['common_issues'].items():
                    print(f"  {issue}: {count} pages")
            
            if hasattr(args, 'output') and args.output:
                analyzer.save_analysis_report(result, args.output, args.format)
                print(f"\nDetailed report saved to: {args.output}")
        
        elif args.command == 'compare':
            result = analyzer.compare_with_working_page(args.problematic_page, args.working_page)
            
            print(f"Comparison: Page {args.problematic_page} vs Page {args.working_page}")
            
            if result['differences']:
                print("Differences found:")
                for diff_type, diff_data in result['differences'].items():
                    print(f"  {diff_type}: {diff_data}")
            
            if result['recommendations']:
                print("Recommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
        
        elif args.command == 'employee':
            result = analyzer.analyze_employee_extraction_issues(args.page_num)
            
            print(f"Employee Extraction Analysis: Page {args.page_num}")
            
            # Pattern results
            for pattern_name, pattern_data in result['employee_patterns'].items():
                if pattern_data['count'] > 0:
                    print(f"  {pattern_name}: {pattern_data['count']} matches")
            
            # OCR issues
            if result['ocr_issues']:
                print(f"  OCR issues: {len(result['ocr_issues'])}")
                if args.verbose:
                    for issue in result['ocr_issues'][:5]:  # Show first 5
                        print(f"    Line {issue['line_num']}: {issue['issue']}")
            
            # Potential employee lines
            if result['potential_employee_lines']:
                print(f"  Potential employee lines not matching patterns: {len(result['potential_employee_lines'])}")
                if args.verbose:
                    for line in result['potential_employee_lines'][:3]:  # Show first 3
                        print(f"    Line {line['line_num']}: {line['line_text'][:50]}...")
            
            # Recommendations
            if result['recommendations']:
                print("Recommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())