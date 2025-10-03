#!/usr/bin/env python3
"""
File Comparison Utility
Consolidated functionality for comparing test-key files with result files.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import csv
import argparse
from typing import List, Dict, Optional, Set, Tuple, Any, Union
from pathlib import Path


class FileComparator:
    """Utility for comparing CSV files and detecting differences."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize with base directory for relative paths."""
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
        self.base_dir = Path(base_dir)
        self.test_keys_dir = self.base_dir / "test-keys"
        self.result_files_dir = self.base_dir / "result-files"
    
    def load_csv_data(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Load CSV data from file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of dictionaries representing rows
        """
        data = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                delimiter = ','
                if ';' in sample and sample.count(';') > sample.count(','):
                    delimiter = ';'
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                for row in reader:
                    # Clean up row data
                    cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                                 for k, v in row.items() if k is not None}
                    data.append(cleaned_row)
        
        except Exception as e:
            raise ValueError(f"Error reading CSV file {file_path}: {e}")
        
        return data
    
    def normalize_key_field(self, value: str) -> str:
        """
        Normalize key fields for comparison (handle OCR errors, spacing, etc.).
        
        Args:
            value: Original value
            
        Returns:
            Normalized value
        """
        if not isinstance(value, str):
            return str(value)
        
        # Basic normalization
        normalized = value.strip().upper()
        
        # Handle common OCR errors
        normalized = normalized.replace('OO-', '00-')  # oo- -> 00-
        normalized = normalized.replace('0O-', '00-')  # 0o- -> 00-
        normalized = normalized.replace('O0-', '00-')  # o0- -> 00-
        
        # Normalize spacing
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def compare_files(self, test_key_file: str, result_file: str, 
                     key_field: str, compare_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare a test-key file with a result file.
        
        Args:
            test_key_file: Path to test-key file
            result_file: Path to result file
            key_field: Field name to use as primary key for comparison
            compare_fields: List of fields to compare (if None, compare all common fields)
            
        Returns:
            Comparison results dictionary
        """
        # Load data
        test_data = self.load_csv_data(test_key_file)
        result_data = self.load_csv_data(result_file)
        
        # Create lookup dictionaries using normalized keys
        test_lookup = {}
        for row in test_data:
            if key_field in row:
                normalized_key = self.normalize_key_field(row[key_field])
                test_lookup[normalized_key] = row
        
        result_lookup = {}
        for row in result_data:
            if key_field in row:
                normalized_key = self.normalize_key_field(row[key_field])
                result_lookup[normalized_key] = row
        
        # Determine fields to compare
        if compare_fields is None:
            test_fields = set(test_data[0].keys() if test_data else set())
            result_fields = set(result_data[0].keys() if result_data else set())
            compare_fields = list(test_fields.intersection(result_fields))
        
        # Find matches and differences
        test_keys = set(test_lookup.keys())
        result_keys = set(result_lookup.keys())
        
        matching_keys = test_keys.intersection(result_keys)
        missing_from_result = test_keys - result_keys
        extra_in_result = result_keys - test_keys
        
        # Compare matching records
        field_differences = []
        matching_records = []
        
        for key in matching_keys:
            test_row = test_lookup[key]
            result_row = result_lookup[key]
            
            row_differences = {}
            for field in compare_fields:
                test_value = test_row.get(field, '')
                result_value = result_row.get(field, '')
                
                # Normalize values for comparison
                test_normalized = str(test_value).strip()
                result_normalized = str(result_value).strip()
                
                if test_normalized != result_normalized:
                    row_differences[field] = {
                        'test_value': test_value,
                        'result_value': result_value
                    }
            
            if row_differences:
                field_differences.append({
                    'key': key,
                    'original_key': test_row[key_field],
                    'differences': row_differences
                })
            else:
                matching_records.append(key)
        
        return {
            'test_file': test_key_file,
            'result_file': result_file,
            'key_field': key_field,
            'compare_fields': compare_fields,
            'summary': {
                'total_test_records': len(test_data),
                'total_result_records': len(result_data),
                'matching_records': len(matching_records),
                'records_with_differences': len(field_differences),
                'missing_from_result': len(missing_from_result),
                'extra_in_result': len(extra_in_result)
            },
            'missing_from_result': list(missing_from_result),
            'extra_in_result': list(extra_in_result),
            'field_differences': field_differences,
            'missing_records_details': [test_lookup[key] for key in missing_from_result],
            'extra_records_details': [result_lookup[key] for key in extra_in_result]
        }
    
    def compare_paystub_files(self, file_type: str = 'earnings') -> Dict[str, Any]:
        """
        Compare paystub processing files using standard naming convention.
        
        Args:
            file_type: Type of file to compare ('earnings', 'deductions', 'tax_deductions')
            
        Returns:
            Comparison results
        """
        # Map file types to expected filenames and key fields
        file_configs = {
            'earnings': {
                'test_key_file': f"{file_type}_key.csv",
                'result_file': f"{file_type}.csv",
                'key_field': 'Page'
            },
            'deductions': {
                'test_key_file': f"{file_type}_key.csv",
                'result_file': f"{file_type}.csv", 
                'key_field': 'Page'
            },
            'tax_deductions': {
                'test_key_file': f"{file_type}_key.csv",
                'result_file': f"{file_type}.csv",
                'key_field': 'Page'
            }
        }
        
        if file_type not in file_configs:
            raise ValueError(f"Unknown file type: {file_type}")
        
        config = file_configs[file_type]
        
        test_key_path = self.test_keys_dir / config['test_key_file']
        result_path = self.result_files_dir / config['result_file']
        
        return self.compare_files(
            str(test_key_path),
            str(result_path),
            config['key_field']
        )
    
    def analyze_missing_entries(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze missing entries to identify patterns.
        
        Args:
            comparison_result: Result from compare_files()
            
        Returns:
            Analysis of missing entries
        """
        missing_records = comparison_result['missing_records_details']
        
        if not missing_records:
            return {'message': 'No missing records to analyze'}
        
        analysis = {
            'total_missing': len(missing_records),
            'missing_by_page': {},
            'patterns': {
                'page_ranges': [],
                'common_categories': {},
                'amount_ranges': {}
            }
        }
        
        # Analyze by page
        for record in missing_records:
            page = record.get('Page', 'Unknown')
            if page not in analysis['missing_by_page']:
                analysis['missing_by_page'][page] = []
            analysis['missing_by_page'][page].append(record)
        
        # Look for page range patterns
        if 'Page' in missing_records[0]:
            pages = [int(record['Page']) for record in missing_records if record.get('Page', '').isdigit()]
            pages.sort()
            
            # Find consecutive page ranges
            ranges = []
            if pages:
                start = pages[0]
                end = pages[0]
                
                for page in pages[1:]:
                    if page == end + 1:
                        end = page
                    else:
                        ranges.append((start, end) if start != end else (start,))
                        start = end = page
                ranges.append((start, end) if start != end else (start,))
            
            analysis['patterns']['page_ranges'] = ranges
        
        # Analyze common categories (for earnings/deductions)
        category_field = None
        for field in ['Category', 'Deduction', 'Tax_Deduction']:
            if field in missing_records[0]:
                category_field = field
                break
        
        if category_field:
            categories = {}
            for record in missing_records:
                category = record.get(category_field, 'Unknown')
                categories[category] = categories.get(category, 0) + 1
            analysis['patterns']['common_categories'] = categories
        
        # Analyze amount ranges
        amount_field = None
        for field in ['Amount', 'Value']:
            if field in missing_records[0]:
                amount_field = field
                break
        
        if amount_field:
            amounts = []
            for record in missing_records:
                try:
                    amount = float(record.get(amount_field, 0))
                    amounts.append(amount)
                except (ValueError, TypeError):
                    continue
            
            if amounts:
                analysis['patterns']['amount_ranges'] = {
                    'min': min(amounts),
                    'max': max(amounts),
                    'avg': sum(amounts) / len(amounts),
                    'count': len(amounts)
                }
        
        return analysis
    
    def generate_comparison_report(self, comparison_result: Dict[str, Any], 
                                 output_file: Optional[str] = None) -> str:
        """
        Generate a detailed comparison report.
        
        Args:
            comparison_result: Result from compare_files()
            output_file: Optional file to save report to
            
        Returns:
            Report text
        """
        report_lines = []
        
        # Header
        report_lines.append("FILE COMPARISON REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Test Key File: {comparison_result['test_file']}")
        report_lines.append(f"Result File: {comparison_result['result_file']}")
        report_lines.append(f"Key Field: {comparison_result['key_field']}")
        report_lines.append(f"Compared Fields: {', '.join(comparison_result['compare_fields'])}")
        report_lines.append("")
        
        # Summary
        summary = comparison_result['summary']
        report_lines.append("SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"Total Test Records: {summary['total_test_records']}")
        report_lines.append(f"Total Result Records: {summary['total_result_records']}")
        report_lines.append(f"Matching Records: {summary['matching_records']}")
        report_lines.append(f"Records with Differences: {summary['records_with_differences']}")
        report_lines.append(f"Missing from Result: {summary['missing_from_result']}")
        report_lines.append(f"Extra in Result: {summary['extra_in_result']}")
        report_lines.append("")
        
        # Missing records
        if comparison_result['missing_from_result']:
            report_lines.append("MISSING FROM RESULT")
            report_lines.append("-" * 30)
            for key in comparison_result['missing_from_result']:
                report_lines.append(f"  {key}")
            report_lines.append("")
        
        # Extra records
        if comparison_result['extra_in_result']:
            report_lines.append("EXTRA IN RESULT")
            report_lines.append("-" * 30)
            for key in comparison_result['extra_in_result']:
                report_lines.append(f"  {key}")
            report_lines.append("")
        
        # Field differences
        if comparison_result['field_differences']:
            report_lines.append("FIELD DIFFERENCES")
            report_lines.append("-" * 30)
            for diff in comparison_result['field_differences']:
                report_lines.append(f"Key: {diff['original_key']}")
                for field, values in diff['differences'].items():
                    report_lines.append(f"  {field}:")
                    report_lines.append(f"    Test:   {values['test_value']}")
                    report_lines.append(f"    Result: {values['result_value']}")
                report_lines.append("")
        
        report_text = '\n'.join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


def main():
    """Command line interface for file comparison utilities."""
    parser = argparse.ArgumentParser(description='File Comparison Utilities')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compare files command
    compare_parser = subparsers.add_parser('compare', help='Compare two CSV files')
    compare_parser.add_argument('test_file', help='Path to test/key file')
    compare_parser.add_argument('result_file', help='Path to result file')
    compare_parser.add_argument('key_field', help='Field name to use as primary key')
    compare_parser.add_argument('--fields', nargs='+', help='Specific fields to compare')
    compare_parser.add_argument('--report', help='Save detailed report to file')
    
    # Compare paystub files command
    paystub_parser = subparsers.add_parser('paystub', help='Compare paystub processing files')
    paystub_parser.add_argument('file_type', choices=['earnings', 'deductions', 'tax_deductions'],
                               help='Type of paystub file to compare')
    paystub_parser.add_argument('--report', help='Save detailed report to file')
    paystub_parser.add_argument('--analyze-missing', action='store_true', 
                               help='Analyze patterns in missing entries')
    
    # Analyze missing command
    missing_parser = subparsers.add_parser('missing', help='Analyze missing entries')
    missing_parser.add_argument('test_file', help='Path to test/key file')
    missing_parser.add_argument('result_file', help='Path to result file')
    missing_parser.add_argument('key_field', help='Field name to use as primary key')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    comparator = FileComparator()
    
    try:
        if args.command == 'compare':
            result = comparator.compare_files(
                args.test_file, 
                args.result_file, 
                args.key_field,
                args.fields
            )
            
            # Print summary
            summary = result['summary']
            print(f"Comparison Results:")
            print(f"  Test records: {summary['total_test_records']}")
            print(f"  Result records: {summary['total_result_records']}")
            print(f"  Matching: {summary['matching_records']}")
            print(f"  With differences: {summary['records_with_differences']}")
            print(f"  Missing from result: {summary['missing_from_result']}")
            print(f"  Extra in result: {summary['extra_in_result']}")
            
            if hasattr(args, 'report') and args.report:
                report = comparator.generate_comparison_report(result, args.report)
                print(f"\nDetailed report saved to: {args.report}")
        
        elif args.command == 'paystub':
            result = comparator.compare_paystub_files(args.file_type)
            
            # Print summary
            summary = result['summary']
            print(f"Paystub {args.file_type} Comparison:")
            print(f"  Test records: {summary['total_test_records']}")
            print(f"  Result records: {summary['total_result_records']}")
            print(f"  Matching: {summary['matching_records']}")
            print(f"  With differences: {summary['records_with_differences']}")
            print(f"  Missing from result: {summary['missing_from_result']}")
            print(f"  Extra in result: {summary['extra_in_result']}")
            
            if hasattr(args, 'analyze_missing') and args.analyze_missing:
                analysis = comparator.analyze_missing_entries(result)
                print(f"\nMissing Entries Analysis:")
                if 'total_missing' in analysis:
                    print(f"  Total missing: {analysis['total_missing']}")
                    if analysis['patterns']['page_ranges']:
                        print(f"  Page ranges: {analysis['patterns']['page_ranges']}")
                    if analysis['patterns']['common_categories']:
                        print(f"  Common categories: {analysis['patterns']['common_categories']}")
                else:
                    print(f"  {analysis['message']}")
            
            if hasattr(args, 'report') and args.report:
                report = comparator.generate_comparison_report(result, args.report)
                print(f"\nDetailed report saved to: {args.report}")
        
        elif args.command == 'missing':
            result = comparator.compare_files(args.test_file, args.result_file, args.key_field)
            analysis = comparator.analyze_missing_entries(result)
            
            print(f"Missing Entries Analysis:")
            if 'total_missing' in analysis:
                print(f"  Total missing: {analysis['total_missing']}")
                if analysis['patterns']['page_ranges']:
                    print(f"  Page ranges: {analysis['patterns']['page_ranges']}")
                if analysis['patterns']['common_categories']:
                    print(f"  Categories: {analysis['patterns']['common_categories']}")
                if analysis['patterns']['amount_ranges']:
                    amounts = analysis['patterns']['amount_ranges']
                    print(f"  Amount range: ${amounts['min']:.2f} - ${amounts['max']:.2f} (avg: ${amounts['avg']:.2f})")
            else:
                print(f"  {analysis['message']}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())