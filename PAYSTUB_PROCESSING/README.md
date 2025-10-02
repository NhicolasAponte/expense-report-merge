# Paystub Processing Module

This directory contains all tools and resources for processing paystub PDF documents and extracting structured data.

## Directory Structure

```
PAYSTUB_PROCESSING/
├── Scripts/
│   ├── extract-paystub-improved.py      # Main production script
│   ├── extract-paystub-clean.py         # Clean CSV generation
│   ├── extract-paystub-structured.py    # Object-oriented approach
│   ├── extract-all-paystub-data.py      # Alternative comprehensive script
│   ├── extract-paystub-data.py          # Original extraction script
│   └── extract-paystub-amounts.py       # Amounts-focused extraction
├── test-files/
│   └── All_22_Paystubs.pdf             # Source paystub document
├── result-files/
│   ├── CSV files (earnings, tax deductions, summaries)
│   └── JSON files (page-by-page extracts)
├── PAYSTUB_PROCESSING_PIPELINE.md      # Detailed technical documentation
└── README.md                           # This file
```

## Quick Start

1. **Navigate to this directory:**
   ```bash
   cd PAYSTUB_PROCESSING
   ```

2. **Run the main processing script:**
   ```bash
   python extract-paystub-improved.py
   ```

3. **Generate clean CSV files:**
   ```bash
   python extract-paystub-clean.py
   ```

## Output Files

Results are saved in the `result-files/` directory:

- **earnings_improved.csv** - All earnings data with hours, amounts, and YTD
- **tax_deductions_improved.csv** - All tax deductions with amounts and YTD
- **clean_earnings.csv** - Cleaned earnings data with employee info
- **clean_tax_deductions.csv** - Cleaned tax deductions with employee info
- **clean_summary.csv** - Summary statistics per employee

## Key Features

- **Crystal Reports Layout Detection** - Handles 3 different PDF layouts automatically
- **Multi-Section Extraction** - Earnings, Tax Deductions, and Deductions
- **Smart Category Filtering** - Removes PDF noise and artifacts
- **Employee Data Linking** - Associates all data with correct employee records
- **Comprehensive Validation** - Error handling and data quality checks

## Dependencies

All scripts use relative paths and import the main config from the parent directory. Make sure you have:

- PyPDF2
- pdfplumber (for structured approach)
- Standard Python libraries (csv, re, os, typing)

## Support

For detailed technical information, see `PAYSTUB_PROCESSING_PIPELINE.md` in this directory.