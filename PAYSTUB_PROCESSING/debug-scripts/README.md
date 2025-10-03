# Debug Scripts Directory

This directory contains consolidated debugging utilities for the paystub processing system. The utilities have been reorganized from individual debug scripts into reusable, modular tools.

## Consolidated Debug Utilities

### 🚀 Quick Start - Master CLI

The easiest way to use all debug utilities is through the master CLI:

```bash
# List all available utilities and commands
python debug_master.py list

# List available workflows
python debug_master.py workflows

# Run a comprehensive page analysis
python debug_master.py workflow page_issues 26

# Debug employee extraction issues
python debug_master.py workflow employee_debug 162

# Validate file outputs
python debug_master.py workflow file_validation earnings
```

### 1. PDF Text Extraction (`pdf_text_utils.py`)

Consolidated functionality for extracting text from PDFs using pdfplumber.

**Features:**
- Extract text from specific pages or page ranges
- Extract specific sections (earnings, deductions, etc.)
- Search for patterns across pages
- Analyze page structure
- Context manager for efficient PDF handling

**Usage Examples:**
```bash
# Extract text from page 26
python pdf_text_utils.py page 26 --lines

# Extract text from page range
python pdf_text_utils.py range 25 27

# Search for pattern across pages
python pdf_text_utils.py search "00-[A-Z]+" --start 1 --end 50

# Extract earnings section from page 26
python pdf_text_utils.py section 26 --start "•••EARNINGS•••" --end "•••DEDUCTIONS•••"

# Analyze page structure
python pdf_text_utils.py analyze 26
```

### 2. Regex Testing Framework (`regex_tester.py`)

Comprehensive framework for testing regex patterns against text data.

**Features:**
- Test patterns on specific pages or text
- Compare multiple patterns
- Validate extraction results
- Test OCR corrections
- Standard paystub patterns included

**Usage Examples:**
```bash
# List available patterns
python regex_tester.py list

# Test employee data pattern on page 26
python regex_tester.py test employee_data_primary --page 26 --verbose

# Compare multiple patterns
python regex_tester.py compare employee_data_primary employee_data_fallback --page 26

# Validate pattern with expected count
python regex_tester.py validate name_date_primary --page 26 --expected-count 1

# Test OCR corrections
python regex_tester.py ocr --page 162
```

### 3. File Comparison Utility (`file_comparator.py`)

Compare test-key files with result files to detect missing entries and differences.

**Features:**
- Compare CSV files with customizable key fields
- Analyze missing entries and patterns
- Generate detailed comparison reports
- Built-in paystub file comparison
- OCR error handling in comparisons

**Usage Examples:**
```bash
# Compare paystub earnings files
python file_comparator.py paystub earnings --analyze-missing

# Compare custom files
python file_comparator.py compare test_key.csv result.csv Page --report comparison_report.txt

# Analyze missing entries patterns
python file_comparator.py missing test_key.csv result.csv Page
```

### 4. Section Analysis Tool (`section_analyzer.py`)

Analyze specific PDF sections (earnings, deductions, tax deductions, employee info).

**Features:**
- Detect section boundaries automatically
- Extract section text
- Validate section data
- Compare pattern effectiveness
- Analyze mixed bullet/asterisk patterns

**Usage Examples:**
```bash
# Analyze earnings section on page 26
python section_analyzer.py analyze 26 earnings --verbose

# Compare patterns for a section
python section_analyzer.py compare 26 earnings

# Validate section extraction
python section_analyzer.py validate 26 earnings --expected-count 5

# Check for mixed patterns
python section_analyzer.py mixed 26

# Extract section text
python section_analyzer.py extract 26 deductions
```

### 5. Page Analysis Tool (`page_analyzer.py`)

Comprehensive analysis of specific problematic pages.

**Features:**
- Complete page analysis (structure, sections, patterns)
- Multi-page analysis with cross-page patterns
- Compare problematic vs working pages
- Employee extraction issue analysis
- Generate JSON/text reports

**Usage Examples:**
```bash
# Comprehensive single page analysis
python page_analyzer.py page 26 --output page_26_analysis.json

# Analyze multiple problematic pages
python page_analyzer.py pages 162 145 107 96 19 --output multi_page_report.txt

# Compare problematic page with working page
python page_analyzer.py compare 162 44

# Analyze employee extraction issues
python page_analyzer.py employee 162 --verbose
```

### 6. Master Debug CLI (`debug_master.py`)

Unified interface for all debug utilities with predefined workflows.

**Features:**
- Single entry point for all utilities
- Predefined workflows for common debugging tasks
- Easy-to-use command structure
- Comprehensive help and examples

**Available Workflows:**
- `page_issues`: Debug general page issues with comprehensive analysis
- `pattern_debug`: Debug specific pattern matching issues
- `file_validation`: Validate output files against test keys
- `comprehensive_page`: Generate comprehensive page analysis report
- `employee_debug`: Debug employee data extraction issues

**Usage Examples:**
```bash
# Debug page issues workflow
python debug_master.py workflow page_issues 26

# Debug specific pattern
python debug_master.py workflow pattern_debug employee_data_primary 26

# Validate earnings file
python debug_master.py workflow file_validation earnings

# Generate comprehensive page report
python debug_master.py workflow comprehensive_page 162

# Debug employee extraction
python debug_master.py workflow employee_debug 162
```

## Key Features of Consolidated System

### 🔧 Modular Design
- Each utility is self-contained and reusable
- Common functionality shared between utilities
- Consistent command-line interfaces

### 📊 Comprehensive Analysis
- Multi-layered analysis (structure, sections, patterns)
- Cross-page pattern analysis
- OCR error detection and correction

### 🎯 Problem-Specific Tools
- Employee extraction debugging
- Section boundary detection
- Pattern validation and comparison
- File output validation

### 📝 Reporting
- JSON and text report formats
- Detailed analysis with recommendations
- Comparison reports with differences highlighted

### 🚀 Workflow Automation
- Predefined workflows for common tasks
- Sequential analysis steps
- Automated report generation

## Common Debugging Scenarios

### Scenario 1: Page Not Extracting Data
```bash
# Run comprehensive page analysis
python debug_master.py workflow page_issues <page_num>

# This will:
# 1. Analyze page structure
# 2. Check all sections
# 3. Test key patterns
# 4. Generate comprehensive report
```

### Scenario 2: Pattern Not Matching
```bash
# Debug specific pattern
python debug_master.py workflow pattern_debug <pattern_name> <page_num>

# This will:
# 1. Test the pattern in detail
# 2. Validate against expectations
# 3. Test OCR corrections
```

### Scenario 3: Missing Results in Output Files
```bash
# Validate file output
python debug_master.py workflow file_validation <file_type>

# This will:
# 1. Compare with test keys
# 2. Analyze missing patterns
# 3. Generate detailed report
```

### Scenario 4: Employee Data Not Extracted
```bash
# Debug employee extraction
python debug_master.py workflow employee_debug <page_num>

# This will:
# 1. Analyze employee-specific patterns
# 2. Check for OCR issues
# 3. Validate section detection
```

## Legacy Scripts (Moved to Archive)

The following individual debug scripts have been consolidated into the utilities above:

### Analysis Scripts (7 files)
- `analyze_earnings_patterns.py` → Use `section_analyzer.py analyze earnings`
- `analyze_missing_deductions.py` → Use `file_comparator.py paystub deductions`
- `analyze_new_pdf.py` → Use `page_analyzer.py pages`
- `analyze_page_44_earnings.py` → Use `section_analyzer.py analyze earnings`
- `analyze_page_45_sections.py` → Use `section_analyzer.py analyze`
- `analyze_pdfplumber_optimization.py` → Use `pdf_text_utils.py analyze`
- `analyze_problematic_pages.py` → Use `page_analyzer.py pages`

### Debug Scripts (4 files)
- `debug_mixed_patterns.py` → Use `section_analyzer.py mixed`
- `debug_page_1.py` → Use `debug_master.py workflow page_issues 1`
- `debug_page_26.py` → Use `debug_master.py workflow page_issues 26`
- `debug_text_extraction.py` → Use `pdf_text_utils.py`

### Test Scripts (7 files)
- `test_earnings_extraction.py` → Use `regex_tester.py test earnings_*`
- `test_employee_extraction.py` → Use `page_analyzer.py employee`
- `test_ocr_corrections.py` → Use `regex_tester.py ocr`
- `test_pattern_priority.py` → Use `regex_tester.py compare`
- `test_pipeline_page26.py` → Use `debug_master.py workflow page_issues 26`
- `test_updated_name_patterns.py` → Use `regex_tester.py test name_*`
- `test_updated_patterns.py` → Use `regex_tester.py test employee_*`

### Utility Scripts (1 file)
- `regenerate_earnings.py` → Use production `paystub_pipeline.py`

### JSON Data Files (3 files)
- `paystub_page_*.json` → Generated by analysis tools as needed

## Benefits of Consolidated System

1. **Reduced Duplication**: Common functionality shared across utilities
2. **Better Organization**: Logical grouping of related functionality  
3. **Improved Usability**: Consistent interfaces and comprehensive help
4. **Enhanced Features**: More powerful analysis capabilities
5. **Workflow Automation**: Predefined sequences for common tasks
6. **Better Documentation**: Clear examples and usage patterns
7. **Maintainability**: Easier to update and extend functionality

## Getting Help

Each utility has built-in help:
```bash
python <utility_name>.py --help
python debug_master.py --help
```

For workflow-specific help:
```bash
python debug_master.py workflows
```
cd ..
python debug-scripts/script_name.py
```

## 📝 Key Issues Resolved

1. **Mixed Pattern Detection** - Fixed bullet/asterisk pattern variations (`***EARNINGS•••`)
2. **Page 1 Missing Data** - Resolved section detection issues for first page
3. **Page 26 Numeric Categories** - Fixed regex to handle `2/700`, `8/900` categories
4. **OCR Employee Numbers** - Added fallback for `oo-` instead of `00-`
5. **OCR Name Issues** - Fixed `111` → `III` and `0.` → `O.` corrections
6. **Employee Name Extraction** - Enhanced patterns for various name formats

## 🔄 Development History

These scripts represent the iterative debugging process that led to a robust paystub processing system capable of handling:
- Various PDF formatting inconsistencies
- OCR reading errors
- Mixed section header patterns
- Numeric category names
- Name suffix variations