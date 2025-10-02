import os
import pdfplumber
from config import LOCAL_DESKTOP_TEMP

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_DIR = TEST_FILES_DIR  # Changed to use test-files directory
# INPUT_DIR = LOCAL_DESKTOP_TEMP  # Original config path

def extract_page_with_layout_v2(page):
    """
    Extract text from a page using pdfplumber's built-in text extraction
    with parameters optimized for layout preservation.
    """
    # Try using pdfplumber's extract_text with custom layout analysis parameters
    text = page.extract_text(
        x_tolerance=3,  # Horizontal tolerance for grouping characters into words
        y_tolerance=3,  # Vertical tolerance for grouping words into lines
        layout=True,   # Try to preserve layout
        x_density=7.25, # Horizontal density for character spacing
        y_density=13   # Vertical density for line spacing
    )
    
    if text:
        # Split into lines and print each non-empty line
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                print(line)
    else:
        print("No text found on this page.")

def extract_page_with_layout_v3(page):
    """
    Alternative approach: Use extract_text_lines method for better line detection.
    """
    try:
        # Use extract_text_lines if available (newer pdfplumber versions)
        if hasattr(page, 'extract_text_lines'):
            text_lines = page.extract_text_lines(
                layout=True,
                x_tolerance=3,
                y_tolerance=3
            )
            for line in text_lines:
                text = line.get('text', '').strip()
                if text:
                    print(text)
        else:
            # Fallback to regular extract_text
            extract_page_with_layout_v2(page)
    except Exception as e:
        print(f"Error in v3 extraction: {e}")
        extract_page_with_layout_v2(page)

def read_pdf_layout_v2(pdf_path):
    """
    Read a PDF file using improved layout analysis.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"File: {os.path.basename(pdf_path)}")
            print(f"Total pages: {num_pages}")
            
            for i, page in enumerate(pdf.pages, start=1):
                print(f"\n--- Page {i} (Method V2) ---")
                extract_page_with_layout_v2(page)
                
                if i == 1:  # Only show comparison for first page
                    print(f"\n--- Page {i} (Method V3) ---")
                    extract_page_with_layout_v3(page)
                
                if i >= 3:  # Limit output for testing
                    break
                    
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")

def main():
    """
    Process all PDF files in the input directory using improved methods.
    """
    if not os.path.exists(INPUT_DIR):
        print(f"Input directory does not exist: {INPUT_DIR}")
        return
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in: {INPUT_DIR}")
        return
    
    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        print("READING PDF WITH IMPROVED LAYOUT ANALYSIS")
        read_pdf_layout_v2(pdf_path)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()