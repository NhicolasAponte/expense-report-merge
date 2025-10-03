# Legacy Debug Scripts

This folder contains the original individual debug scripts that were used during development. These scripts have been consolidated into the new unified debug utilities in the parent directory.

## Migration Guide

All functionality from these legacy scripts has been moved to the new consolidated utilities:

### Analysis Scripts → New Utilities
- `analyze_earnings_patterns.py` → `section_analyzer.py analyze earnings`
- `analyze_missing_deductions.py` → `file_comparator.py paystub deductions`
- `analyze_new_pdf.py` → `page_analyzer.py pages`
- `analyze_page_44_earnings.py` → `section_analyzer.py analyze earnings` + page 44
- `analyze_page_45_sections.py` → `section_analyzer.py analyze` + page 45
- `analyze_pdfplumber_optimization.py` → `pdf_text_utils.py analyze`
- `analyze_problematic_pages.py` → `page_analyzer.py pages 162 145 107 96 19`

### Debug Scripts → New Utilities
- `debug_mixed_patterns.py` → `section_analyzer.py mixed`
- `debug_page_1.py` → `debug_master.py workflow page_issues 1`
- `debug_page_26.py` → `debug_master.py workflow page_issues 26`
- `debug_text_extraction.py` → `pdf_text_utils.py`

### Test Scripts → New Utilities
- `test_earnings_extraction.py` → `regex_tester.py test earnings_category_numeric`
- `test_employee_extraction.py` → `page_analyzer.py employee`
- `test_ocr_corrections.py` → `regex_tester.py ocr`
- `test_pattern_priority.py` → `regex_tester.py compare`
- `test_pipeline_page26.py` → `debug_master.py workflow page_issues 26`
- `test_updated_name_patterns.py` → `regex_tester.py test name_date_primary`
- `test_updated_patterns.py` → `regex_tester.py test employee_data_primary employee_data_fallback`

### Utility Scripts → Production Code
- `regenerate_earnings.py` → Use production `paystub_pipeline.py`

## Using the New System

Instead of running individual scripts, use the new consolidated system:

```bash
# For comprehensive page analysis (replaces most debug scripts)
python ../debug_master.py workflow page_issues <page_num>

# For pattern testing (replaces test scripts)
python ../regex_tester.py test <pattern_name> --page <page_num>

# For file validation (replaces analysis scripts)
python ../file_comparator.py paystub <file_type>

# For section analysis (replaces section-specific scripts)
python ../section_analyzer.py analyze <page_num> <section_type>
```

## Benefits of New System

1. **Consolidated**: No need to remember 22 different script names
2. **Consistent**: All utilities have similar command-line interfaces
3. **Powerful**: More features and better analysis capabilities
4. **Workflows**: Predefined sequences for common debugging tasks
5. **Maintainable**: Easier to update and extend functionality

## Legacy File Inventory

- **7 Analysis Scripts**: Moved to section_analyzer.py and page_analyzer.py
- **4 Debug Scripts**: Moved to debug_master.py workflows and utilities
- **7 Test Scripts**: Moved to regex_tester.py and page_analyzer.py
- **1 Utility Script**: Functionality moved to production pipeline
- **3 JSON Files**: Generated dynamically by new utilities

These files are kept for reference but should not be used for new development.