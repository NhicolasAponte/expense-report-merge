#!/usr/bin/env python3
"""
Debug Master CLI
Master command-line interface that calls all the consolidated debug utilities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import subprocess
from typing import List, Dict, Optional, Any
from pathlib import Path


class DebugMaster:
    """Master interface for all debug utilities."""
    
    def __init__(self):
        """Initialize debug master."""
        self.debug_dir = Path(__file__).parent
        self.utilities = {
            'pdf_text_utils': {
                'file': 'pdf_text_utils.py',
                'description': 'PDF text extraction utilities',
                'commands': ['page', 'range', 'section', 'search', 'analyze']
            },
            'regex_tester': {
                'file': 'regex_tester.py',
                'description': 'Regex pattern testing framework',
                'commands': ['test', 'compare', 'validate', 'list', 'ocr']
            },
            'file_comparator': {
                'file': 'file_comparator.py',
                'description': 'File comparison utilities',
                'commands': ['compare', 'paystub', 'missing']
            },
            'section_analyzer': {
                'file': 'section_analyzer.py',
                'description': 'Section analysis tools',
                'commands': ['analyze', 'compare', 'validate', 'mixed', 'extract']
            },
            'page_analyzer': {
                'file': 'page_analyzer.py',
                'description': 'Page analysis tools',
                'commands': ['page', 'pages', 'compare', 'employee']
            }
        }
    
    def run_utility(self, utility_name: str, command: str, args: List[str]) -> int:
        """
        Run a specific utility command.
        
        Args:
            utility_name: Name of utility to run
            command: Command to execute
            args: Additional arguments
            
        Returns:
            Exit code
        """
        if utility_name not in self.utilities:
            print(f"Error: Unknown utility '{utility_name}'")
            print(f"Available utilities: {', '.join(self.utilities.keys())}")
            return 1
        
        utility_config = self.utilities[utility_name]
        utility_file = self.debug_dir / utility_config['file']
        
        if not utility_file.exists():
            print(f"Error: Utility file not found: {utility_file}")
            return 1
        
        # Build command
        cmd = [sys.executable, str(utility_file), command] + args
        
        try:
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode
        except Exception as e:
            print(f"Error running utility: {e}")
            return 1
    
    def list_utilities(self) -> None:
        """List all available utilities and their commands."""
        print("Debug Utilities Available:")
        print("=" * 50)
        
        for utility_name, config in self.utilities.items():
            print(f"\n{utility_name}: {config['description']}")
            print(f"  Commands: {', '.join(config['commands'])}")
            print(f"  Usage: debug_master.py {utility_name} <command> [args...]")
    
    def run_workflow(self, workflow_name: str, args: List[str]) -> int:
        """
        Run predefined workflows for common debugging tasks.
        
        Args:
            workflow_name: Name of workflow to run
            args: Workflow-specific arguments
            
        Returns:
            Exit code
        """
        workflows = {
            'page_issues': self._workflow_page_issues,
            'pattern_debug': self._workflow_pattern_debug,
            'file_validation': self._workflow_file_validation,
            'comprehensive_page': self._workflow_comprehensive_page,
            'employee_debug': self._workflow_employee_debug
        }
        
        if workflow_name not in workflows:
            print(f"Error: Unknown workflow '{workflow_name}'")
            print(f"Available workflows: {', '.join(workflows.keys())}")
            return 1
        
        try:
            return workflows[workflow_name](args)
        except Exception as e:
            print(f"Error running workflow: {e}")
            return 1
    
    def _workflow_page_issues(self, args: List[str]) -> int:
        """Workflow for debugging page issues."""
        if len(args) < 1:
            print("Usage: debug_master.py workflow page_issues <page_num> [pdf_path]")
            return 1
        
        page_num = args[0]
        pdf_args = ['--pdf', args[1]] if len(args) > 1 else []
        
        print(f"=== PAGE ISSUES WORKFLOW: Page {page_num} ===\n")
        
        # 1. Basic page structure
        print("1. Analyzing page structure...")
        result = self.run_utility('pdf_text_utils', 'analyze', [page_num] + pdf_args)
        if result != 0:
            return result
        
        print("\n" + "-" * 50 + "\n")
        
        # 2. Section analysis
        print("2. Analyzing sections...")
        for section in ['earnings', 'deductions', 'tax_deductions', 'employee_info']:
            print(f"\n--- {section.upper()} SECTION ---")
            self.run_utility('section_analyzer', 'analyze', [page_num, section] + pdf_args)
        
        print("\n" + "-" * 50 + "\n")
        
        # 3. Pattern testing
        print("3. Testing key patterns...")
        for pattern in ['employee_data_primary', 'employee_data_fallback', 'name_date_primary']:
            print(f"\n--- {pattern.upper()} PATTERN ---")
            self.run_utility('regex_tester', 'test', [pattern, '--page', page_num] + pdf_args)
        
        print("\n" + "-" * 50 + "\n")
        
        # 4. Comprehensive page analysis
        print("4. Comprehensive page analysis...")
        self.run_utility('page_analyzer', 'page', [page_num] + pdf_args)
        
        return 0
    
    def _workflow_pattern_debug(self, args: List[str]) -> int:
        """Workflow for debugging pattern issues."""
        if len(args) < 2:
            print("Usage: debug_master.py workflow pattern_debug <pattern_name> <page_num> [pdf_path]")
            return 1
        
        pattern_name = args[0]
        page_num = args[1]
        pdf_args = ['--pdf', args[2]] if len(args) > 2 else []
        
        print(f"=== PATTERN DEBUG WORKFLOW: {pattern_name} on page {page_num} ===\n")
        
        # 1. Test the pattern
        print("1. Testing pattern...")
        result = self.run_utility('regex_tester', 'test', [pattern_name, '--page', page_num, '--verbose'] + pdf_args)
        if result != 0:
            return result
        
        print("\n" + "-" * 50 + "\n")
        
        # 2. Validate pattern
        print("2. Validating pattern...")
        self.run_utility('regex_tester', 'validate', [pattern_name, '--page', page_num] + pdf_args)
        
        print("\n" + "-" * 50 + "\n")
        
        # 3. Test OCR corrections
        print("3. Testing OCR corrections...")
        self.run_utility('regex_tester', 'ocr', ['--page', page_num] + pdf_args)
        
        return 0
    
    def _workflow_file_validation(self, args: List[str]) -> int:
        """Workflow for validating output files."""
        if len(args) < 1:
            print("Usage: debug_master.py workflow file_validation <file_type>")
            print("File types: earnings, deductions, tax_deductions")
            return 1
        
        file_type = args[0]
        
        print(f"=== FILE VALIDATION WORKFLOW: {file_type} ===\n")
        
        # 1. Compare files
        print("1. Comparing files...")
        result = self.run_utility('file_comparator', 'paystub', [file_type, '--analyze-missing'])
        if result != 0:
            return result
        
        print("\n" + "-" * 50 + "\n")
        
        # 2. Generate detailed report
        print("2. Generating detailed report...")
        report_file = f"{file_type}_comparison_report.txt"
        self.run_utility('file_comparator', 'paystub', [file_type, '--report', report_file])
        print(f"Detailed report saved to: {report_file}")
        
        return 0
    
    def _workflow_comprehensive_page(self, args: List[str]) -> int:
        """Comprehensive analysis of a page."""
        if len(args) < 1:
            print("Usage: debug_master.py workflow comprehensive_page <page_num> [pdf_path]")
            return 1
        
        page_num = args[0]
        pdf_args = ['--pdf', args[1]] if len(args) > 1 else []
        
        print(f"=== COMPREHENSIVE PAGE ANALYSIS: Page {page_num} ===\n")
        
        # Generate comprehensive report
        report_file = f"page_{page_num}_comprehensive_report.json"
        result = self.run_utility('page_analyzer', 'page', [page_num, '--output', report_file, '--format', 'json'] + pdf_args)
        
        if result == 0:
            print(f"\nComprehensive report saved to: {report_file}")
        
        return result
    
    def _workflow_employee_debug(self, args: List[str]) -> int:
        """Workflow for debugging employee extraction issues."""
        if len(args) < 1:
            print("Usage: debug_master.py workflow employee_debug <page_num> [pdf_path]")
            return 1
        
        page_num = args[0]
        pdf_args = ['--pdf', args[1]] if len(args) > 1 else []
        
        print(f"=== EMPLOYEE DEBUG WORKFLOW: Page {page_num} ===\n")
        
        # 1. Employee-specific analysis
        print("1. Employee extraction analysis...")
        result = self.run_utility('page_analyzer', 'employee', [page_num, '--verbose'] + pdf_args)
        if result != 0:
            return result
        
        print("\n" + "-" * 50 + "\n")
        
        # 2. Test employee patterns
        print("2. Testing employee patterns...")
        for pattern in ['employee_data_primary', 'employee_data_fallback']:
            print(f"\n--- {pattern} ---")
            self.run_utility('regex_tester', 'test', [pattern, '--page', page_num] + pdf_args)
        
        print("\n" + "-" * 50 + "\n")
        
        # 3. Employee info section analysis
        print("3. Employee info section analysis...")
        self.run_utility('section_analyzer', 'analyze', [page_num, 'employee_info'] + pdf_args)
        
        return 0
    
    def list_workflows(self) -> None:
        """List available workflows."""
        workflows = {
            'page_issues': 'Debug general page issues with comprehensive analysis',
            'pattern_debug': 'Debug specific pattern matching issues', 
            'file_validation': 'Validate output files against test keys',
            'comprehensive_page': 'Generate comprehensive page analysis report',
            'employee_debug': 'Debug employee data extraction issues'
        }
        
        print("Available Workflows:")
        print("=" * 50)
        
        for workflow_name, description in workflows.items():
            print(f"\n{workflow_name}: {description}")
            print(f"  Usage: debug_master.py workflow {workflow_name} [args...]")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Debug Master CLI - Unified interface for all debug utilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all utilities
  debug_master.py list
  
  # Run specific utility command
  debug_master.py pdf_text_utils page 26
  debug_master.py regex_tester test employee_data_primary --page 26
  debug_master.py file_comparator paystub earnings
  debug_master.py section_analyzer analyze 26 earnings
  debug_master.py page_analyzer page 26
  
  # Run predefined workflows
  debug_master.py workflow page_issues 26
  debug_master.py workflow pattern_debug employee_data_primary 26
  debug_master.py workflow file_validation earnings
  
  # List available workflows
  debug_master.py workflows
        """
    )
    
    subparsers = parser.add_subparsers(dest='action', help='Available actions')
    
    # List utilities
    list_parser = subparsers.add_parser('list', help='List all available utilities')
    
    # List workflows  
    workflows_parser = subparsers.add_parser('workflows', help='List all available workflows')
    
    # Run workflow
    workflow_parser = subparsers.add_parser('workflow', help='Run a predefined workflow')
    workflow_parser.add_argument('workflow_name', help='Name of workflow to run')
    workflow_parser.add_argument('args', nargs='*', help='Workflow arguments')
    
    # Run utility commands
    for utility_name, config in DebugMaster().utilities.items():
        utility_parser = subparsers.add_parser(utility_name, help=config['description'])
        utility_parser.add_argument('command', help='Command to run')
        utility_parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return 0
    
    master = DebugMaster()
    
    try:
        if args.action == 'list':
            master.list_utilities()
            return 0
        
        elif args.action == 'workflows':
            master.list_workflows()
            return 0
        
        elif args.action == 'workflow':
            return master.run_workflow(args.workflow_name, args.args)
        
        elif args.action in master.utilities:
            return master.run_utility(args.action, args.command, args.args)
        
        else:
            print(f"Unknown action: {args.action}")
            return 1
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())