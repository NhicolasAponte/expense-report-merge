# Paystub PDF Processing Pipeline Summary

## Overview
This pipeline processes multi-page PDF paystub documents to extract structured data from three main sections: Earnings, Tax Deductions, and Deductions. The system handles Crystal Reports columnar layouts with intelligent layout detection and accurate data mapping.

## Project Structure
```
PAYSTUB_PROCESSING/
├── extract-paystub-improved.py         # Main production script
├── extract-all-paystub-data.py         # Alternative comprehensive approach  
├── extract-paystub-structured.py       # Object-oriented dataclass approach
├── extract-paystub-clean.py            # Clean CSV generation
├── extract-paystub-data.py             # Original extraction script
├── extract-paystub-amounts.py          # Amounts-focused extraction
├── test-files/
│   └── All_22_Paystubs.pdf            # Source paystub document
├── result-files/
│   ├── clean_earnings.csv             # Clean earnings data
│   ├── clean_tax_deductions.csv       # Clean tax deductions data
│   ├── clean_summary.csv              # Summary statistics
│   ├── earnings.csv                   # Raw earnings extraction
│   ├── tax_deductions.csv             # Raw tax deductions
│   ├── paystub_data.csv               # Combined raw data
│   └── paystub_page_*.json            # Page-by-page JSON extracts
└── PAYSTUB_PROCESSING_PIPELINE.md     # This documentation
```

## Input Data
- **Source File**: `test-files/All_22_Paystubs.pdf` (53 pages, 22+ employees)
- **Format**: Crystal Reports generated PDF with varying columnar layouts
- **Sections**: EARNINGS, TAX DEDUCTIONS, DEDUCTIONS

## Core Processing Scripts

### 1. Primary Production Script
**File**: `extract-paystub-improved.py`
- **Purpose**: Main production script with Crystal Reports layout detection
- **Key Functions**:
  - `main()` - Entry point, orchestrates full processing
  - `process_earnings_page()` - Extracts earnings with hours, amount, YTD
  - `process_tax_deductions_page()` - Extracts tax deductions with amount, YTD
  - `process_deductions_page()` - Extracts other deductions with amount, YTD
  - `detect_layout_pattern()` - Identifies one of three Crystal Reports layouts
  - `extract_layout_a_data()` - Handles combined Amount/YTD pairs after single YTD header
  - `extract_layout_b_data()` - Handles separate Amount and YTD columns
  - `extract_layout_c_data()` - Handles combined 'Amount YTD' header with pairs
  - `extract_employee_data_from_page()` - Gets employee name, number, period end
  - `export_to_csv()` - Exports data to CSV files with data type specification

### 2. Comprehensive Alternative Script
**File**: `extract-all-paystub-data.py`
- **Purpose**: Alternative comprehensive extraction approach
- **Key Functions**:
  - `extract_earnings_categories()` - Identifies earnings category names
  - `extract_tax_deductions_categories()` - Identifies tax deduction categories
  - `extract_deductions_categories()` - Identifies other deduction categories
  - `process_page()` - Single page processing for all three sections

### 3. Structured Object-Oriented Approach
**File**: `extract-paystub-structured.py`
- **Purpose**: Clean, object-oriented extraction using dataclasses
- **Key Classes**:
  - `PaystubItem` - Single line item (name, hours, amount, ytd)
  - `PaystubData` - Complete paystub record with all sections
  - `PaystubExtractor` - Main extraction class with regex patterns
- **Key Functions**:
  - `extract_paystub_data()` - Main extraction method
  - `extract_section_items()` - Generic section extraction
  - `parse_amount()` - Clean monetary value parsing

### 4. Clean CSV Generation Script
**File**: `extract-paystub-clean.py`
- **Purpose**: Generates clean, formatted CSV outputs
- **Key Functions**:
  - `create_earnings_csv()` - Creates clean earnings CSV
  - `create_tax_deductions_csv()` - Creates clean tax deductions CSV
  - `create_summary_csv()` - Creates employee summary CSV
  - `main()` - Orchestrates clean CSV generation

## Crystal Reports Layout Detection System

### Layout Patterns Identified:
1. **Layout A**: Combined Amount/YTD pairs after single YTD header
   - Format: Single "YTD" column header followed by "amount ytd" pairs
   - Example: Glass: 683.95 4,828.69

2. **Layout B**: Separate Amount and YTD columns  
   - Format: Distinct "Amount" and "YTD" column headers
   - Example: Amount column: 683.95, YTD column: 4,828.69

3. **Layout C**: Combined 'Amount YTD' header with pairs
   - Format: "Amount YTD" header followed by paired values
   - Example: Admin.: 1,000.00 41,133.36

## Data Extraction Functions

### Employee Data Extraction:
- `extract_employee_data_from_page()` - Gets basic employee information
- `_is_valid_name()` - Validates employee names vs company data
- Pattern matching for employee number, period end date (9/13/2025)

### Category Extraction:
- `extract_earnings_categories()` - Identifies earning types (Glass, Admin, etc.)
- `extract_tax_deductions_categories()` - Identifies tax categories with regex patterns
- `extract_deductions_categories()` - Identifies other deduction categories

### Financial Data Extraction:
- `extract_hours_column()` - Gets hours worked (earnings only)
- `extract_layout_a_data()` - Parses combined amount/YTD pairs
- `extract_layout_b_data()` - Extracts from separate columns
- `extract_layout_c_data()` - Handles combined header format

## Output Generation

### CSV Files Produced:
1. **earnings_improved.csv**
   - Columns: filename, page_number, employee_name, employee_number, period_end, category, hours, amount, ytd
   - Records: 215 earnings records across 26 categories

2. **tax_deductions_improved.csv**
   - Columns: filename, page_number, employee_name, employee_number, period_end, category, amount, ytd
   - Records: 433 tax deduction records across 41 categories

3. **deductions_improved.csv**
   - Columns: filename, page_number, employee_name, employee_number, period_end, category, amount, ytd
   - Records: 0 (no non-tax deductions found in this document format)

### Data Categories Extracted:

#### Earnings Categories (26):
Admin, Bevel, Bevel-OT, Doors, Equip Mtce, Equip Mtce-OT, Glass, Holiday, Jury Duty, Loaders, Metal, Metal-OT, Metal-OT Paid Time Off, Mileage, OT Doors, OT Glass, OT-Loader, OTAdmin, Paid Time Off, Paid Time Off Payout, Referral Bonus, TD-Stops, Truck Driver, Truck Driver Overnight, Truck Driver-OT, Truck Driver-RACKS

#### Tax Deduction Categories (41):
401K Pre-tax Deduction, 401K Roth Deduction, Aflac (Accident, Cancer, Hospital, Short Term Disability, Specified Event), Central Bank, Chase Bank, Child Support, Collins Community CU, Community 1st Credit Union, Community Choice CU, Dental Employee (Child/Family/Spouse), Federal W/H, Green State variations, Health Employee (Child/Spouse), IAStateW/H, Journey Credit Union, Life Insurance, Marine Credit Union, Medicare Tax, Premier CU/Credit Union, Social Security Tax, Stride Bank, US Bank, Veridian/Verdian CU variations, Vision (Member, Family, Child, One)

## Processing Workflow

### 1. Initialization
```python
INPUT_FILE = "test-files/All_22_Paystubs.pdf"
OUTPUT_DIR = "test-files/"
```

### 2. Page Processing Loop
```python
for page_num in range(1, len(reader.pages) + 1):
    page = reader.pages[page_num - 1]
    
    # Extract each section
    earnings_data = process_earnings_page(page, page_num, filename)
    tax_deductions_data = process_tax_deductions_page(page, page_num, filename)
    deductions_data = process_deductions_page(page, page_num, filename)
```

### 3. Data Export
```python
export_to_csv(all_earnings_data, 'earnings_improved.csv', 'earnings')
export_to_csv(all_tax_deductions_data, 'tax_deductions_improved.csv', 'tax deductions')
export_to_csv(all_deductions_data, 'deductions_improved.csv', 'deductions')
```

## Error Handling & Validation

### Layout Detection Validation:
- Handles unknown layout patterns gracefully
- Fallback mechanisms for missing data
- Comprehensive logging of processing status

### Data Validation:
- Employee name validation against company data patterns
- Amount/YTD pairing verification
- Period end date consistency checking (9/13/2025 standard)

### Error Recovery:
- Page-level error isolation (failed pages don't stop processing)
- Detailed error reporting with page numbers
- Graceful handling of permission errors on file writes

## Performance Metrics

### Processing Results:
- **Total Pages**: 53 pages processed
- **Earnings Records**: 215 successfully extracted
- **Tax Deduction Records**: 433 successfully extracted  
- **Processing Success Rate**: 100% page coverage
- **Layout Detection**: 3 patterns successfully identified and handled

### Processing Time Considerations:
- PDF text extraction per page
- Regex pattern matching for category identification
- Layout detection algorithm execution
- CSV file generation and writing

## Usage Examples

### Basic Usage (run from PAYSTUB_PROCESSING directory):
```bash
cd PAYSTUB_PROCESSING
python extract-paystub-improved.py
```

### Clean CSV Generation:
```bash
python extract-paystub-clean.py
```

### Structured Object Approach:
```bash
python extract-paystub-structured.py
```

## Configuration & Dependencies

### Required Libraries:
- `PyPDF2` - PDF text extraction
- `pdfplumber` - Alternative PDF processing (structured approach)
- `csv` - CSV file generation
- `re` - Regular expression processing
- `os` - File system operations
- `typing` - Type hint support

### Configuration Files:
- `../config.py` - Path and environment configurations (in parent directory)
- `../requirements.txt` - Python package dependencies (in parent directory)

### File Paths:
All scripts use relative paths within the PAYSTUB_PROCESSING folder structure:
- Input: `test-files/All_22_Paystubs.pdf`
- Output: `result-files/*.csv` and `result-files/*.json`

### Input/Output Directories:
- Input: `test-files/All_22_Paystubs.pdf`
- Output: `test-files/*.csv`
- Validation: `test-keys/earnings_key.csv` (reference data)

## Quality Assurance

### Validation Methods:
- Comparison against manually created key files
- Cross-validation between different extraction approaches
- Amount/YTD sum verification
- Employee data consistency checks

### Known Issues Resolved:
1. ✅ Amount/YTD value swapping in different layouts
2. ✅ Missing data on certain pages (Page 3 issue resolved)
3. ✅ Incorrect period end date extraction
4. ✅ Employee name vs company name confusion
5. ✅ Tax deduction category filtering (noise removal)

This pipeline successfully extracts comprehensive paystub data with high accuracy and handles the complexities of Crystal Reports PDF formatting through intelligent layout detection and robust data processing methods.