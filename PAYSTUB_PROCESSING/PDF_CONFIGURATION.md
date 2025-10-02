# Paystub Processing - Configuration Guide

## PDF File Configuration

The paystub processing system has been updated to work with any PDF file, removing hardcoded references to specific filenames.

### Auto-Detection

By default, all scripts will automatically detect and use the first available PDF file in the `test-files/` directory:

```bash
# Uses auto-detected PDF from test-files/
python paystub_pipeline.py

# Analysis scripts also support auto-detection  
python analyze_page_44_earnings.py
```

### Specifying Custom PDF Files

You can specify any PDF file path as an argument:

```bash
# Use specific PDF file
python paystub_pipeline.py path/to/your/paystubs.pdf

# With output directory
python paystub_pipeline.py path/to/your/paystubs.pdf --output-dir custom_output/

# Analysis scripts accept PDF path too
python analyze_page_44_earnings.py path/to/your/paystubs.pdf
```

### Available PDF Files

Currently available in `test-files/`:
- `All_20_Paystubs.pdf` (13 pages, 20 employees)

### Common Utilities

The system now includes `common_utils.py` with shared functions:
- `get_pdf_path()` - Auto-detects or validates PDF paths
- `setup_output_directory()` - Creates output directories
- `get_pdf_filename_without_extension()` - Extracts base filename

### Updated Scripts

All the following scripts now support configurable PDF paths:
- `paystub_pipeline.py` - Main processing pipeline
- `analyze_page_44_earnings.py` - Page 44 earnings analysis
- `analyze_missing_deductions.py` - Deductions analysis
- `analyze_page_45_sections.py` - Section boundary analysis
- `test_pattern_priority.py` - Pattern testing
- `extract-paystub-amounts.py` - Amount extraction
- And all other analysis/test scripts

### Migration Notes

- **CSV Output**: The filename column in output CSV files will now reflect the actual PDF filename being processed
- **Backwards Compatibility**: All scripts maintain their existing functionality while adding PDF path flexibility
- **Error Handling**: Clear error messages if PDF files are not found

## Usage Examples

```bash
# Process any PDF file
python paystub_pipeline.py "January_2024_Paystubs.pdf"

# Use different output directory  
python paystub_pipeline.py "Q1_Paystubs.pdf" --output-dir "quarterly_results/"

# Run analysis on custom PDF
python analyze_page_44_earnings.py "new_paystubs.pdf"
```