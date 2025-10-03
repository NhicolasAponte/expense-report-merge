# Paystub Processing Module

This directory contains all tools and resources for processing paystub PDF documents and extracting structured data.

**IMPORTANT**: All production scripts now use **pdfplumber** as the primary PDF text extraction method for better accuracy and layout preservation.

## Directory Structure

```
PAYSTUB_PROCESSING/
├── Scripts/
│   ├── paystub_pipeline.py              # RECOMMENDED: Main production pipeline (pdfplumber)
│   ├── extract-paystub-clean.py         # Clean CSV generation (pdfplumber)
│   ├── extract-paystub-structured.py    # Object-oriented approach (pdfplumber)
│   ├── extract-paystub-improved.py      # DEPRECATED: Use paystub_pipeline.py instead
│   ├── extract-all-paystub-data.py      # DEPRECATED: Use paystub_pipeline.py instead
│   ├── extract-paystub-data.py          # DEPRECATED: Use paystub_pipeline.py instead
│   └── extract-paystub-amounts.py       # DEPRECATED: Use paystub_pipeline.py instead
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

2. **Run the RECOMMENDED main processing pipeline:**
   ```bash
   python paystub_pipeline.py
   ```

3. **Alternative: Generate clean CSV files:**
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
- **pdfplumber Integration** - Better text extraction and layout preservation

## Dependencies

All scripts use relative paths and import the main config from the parent directory. Make sure you have:

- **pdfplumber** (primary PDF extraction library - RECOMMENDED)
- PyPDF2 (legacy support only - being phased out)
- Standard Python libraries (csv, re, os, typing)

## Support

For detailed technical information, see `PAYSTUB_PROCESSING_PIPELINE.md` in this directory.