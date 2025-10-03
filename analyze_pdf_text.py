import os
import re
from PyPDF2 import PdfReader

# Path to the PDF file
PDF_PATH = os.path.join(os.path.dirname(__file__), "test-files", "All_20_Paystubs.pdf")

def extract_and_analyze_all_pages():
    """Extract raw text from all pages and analyze patterns"""
    try:
        reader = PdfReader(PDF_PATH)
        total_pages = len(reader.pages)
        
        print(f"📄 Analyzing PDF: {os.path.basename(PDF_PATH)}")
        print(f"📊 Total pages: {total_pages}")
        print("=" * 80)
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            
            print(f"\n🔍 PAGE {page_num}")
            print("-" * 40)
            
            if not text.strip():
                print("❌ No text found on this page")
                continue
                
            # Show raw text (first 500 characters)
            print("📝 RAW TEXT (first 500 chars):")
            print(repr(text[:500]))
            print("\n📝 FORMATTED TEXT (first 1000 chars):")
            print(text[:1000])
            print("\n" + "=" * 40)
            
            # Analyze specific patterns
            analyze_page_patterns(text, page_num)
            
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")

def analyze_page_patterns(text, page_num):
    """Analyze specific patterns on a page"""
    print(f"🔍 PATTERN ANALYSIS FOR PAGE {page_num}:")
    
    # Current regex patterns from the script
    patterns = {
        'employee_name_1': r'[A-Z]{2}\s+\d{5}\s*\n([A-Za-z\s\.]+?)\s*\n',
        'employee_name_2': r'\d{1,2}/\d{1,2}/\d{4}([A-Za-z\s\.]+?)\d{4}',
        'pay_rate_1': r'Pay Rate\s*\n(\d+\.\d+)\s*HW',
        'pay_rate_2': r'HW(\d+\.\d+)',
        'emp_number_1': r'Employee Number\s*\n([0-9]{2}-[A-Z]+)',
        'emp_number_2': r'YTD([0-9]{2}-[A-Z]+)\*\*\*',
        'stub_number_1': r'Stub Number\s*\n([A-Z0-9]+)',
        'stub_number_2': r'Stub Number([A-Z0-9]+)Hours',
        'period_end_1': r'Period End\s*\n(\d{1,2}/\d{1,2}/\d{4})',
        'period_end_2': r'(\d{1,2}/\d{1,2}/\d{4}).*?Period End'
    }
    
    found_matches = {}
    
    for pattern_name, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        match_list = [(m.group(), m.span()) for m in matches]
        if match_list:
            found_matches[pattern_name] = match_list
            print(f"   ✅ {pattern_name}: {match_list}")
        else:
            print(f"   ❌ {pattern_name}: No matches")
    
    # Look for potential employee names (broader search)
    print("\n🔍 BROADER NAME SEARCH:")
    name_patterns = [
        r'([A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+)',  # First Middle Last
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last
        r'([A-Z][A-Za-z\s\.]{10,40})',  # Any capitalized text 10-40 chars
    ]
    
    for i, pattern in enumerate(name_patterns, 1):
        matches = re.finditer(pattern, text)
        match_list = [(m.group(1), m.span()) for m in matches]
        if match_list:
            print(f"   Name Pattern {i}: {match_list}")
    
    # Look for potential employee numbers
    print("\n🔍 BROADER EMPLOYEE NUMBER SEARCH:")
    emp_patterns = [
        r'([0-9]{2}-[A-Z]+)',  # XX-ABC format
        r'([0-9]{2}[A-Z]+)',   # XXABC format
        r'([0-9]+[A-Z]{2,})',  # Numbers followed by letters
    ]
    
    for i, pattern in enumerate(emp_patterns, 1):
        matches = re.finditer(pattern, text)
        match_list = [(m.group(1), m.span()) for m in matches]
        if match_list:
            print(f"   Emp Number Pattern {i}: {match_list}")
    
    # Look for potential pay rates
    print("\n🔍 BROADER PAY RATE SEARCH:")
    pay_patterns = [
        r'(\d+\.\d+)',  # Any decimal number
        r'HW(\d+\.\d+)',  # HW followed by decimal
        r'(\d+\.\d+)\s*HW',  # Decimal followed by HW
        r'Rate.*?(\d+\.\d+)',  # "Rate" followed by decimal
    ]
    
    for i, pattern in enumerate(pay_patterns, 1):
        matches = re.finditer(pattern, text)
        match_list = [(m.group(), m.span()) for m in matches]
        if match_list:
            print(f"   Pay Rate Pattern {i}: {match_list[:5]}")  # Limit to first 5 matches
    
    # Look for stub numbers
    print("\n🔍 BROADER STUB NUMBER SEARCH:")
    stub_patterns = [
        r'(D[0-9]+)',  # D followed by numbers
        r'([A-Z][0-9]{8,})',  # Letter followed by 8+ numbers
        r'Stub.*?([A-Z0-9]{8,})',  # "Stub" followed by alphanumeric
    ]
    
    for i, pattern in enumerate(stub_patterns, 1):
        matches = re.finditer(pattern, text)
        match_list = [(m.group(1), m.span()) for m in matches]
        if match_list:
            print(f"   Stub Pattern {i}: {match_list}")

if __name__ == "__main__":
    extract_and_analyze_all_pages()