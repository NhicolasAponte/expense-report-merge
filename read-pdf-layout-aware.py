import os
import pdfplumber
from config import LOCAL_DESKTOP_TEMP

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_DIR = TEST_FILES_DIR  # Changed to use test-files directory
# INPUT_DIR = LOCAL_DESKTOP_TEMP  # Original config path

# Tolerance for grouping words into the same line (pixels)
Y_TOLERANCE = 5  # Increased tolerance to better group words on same line

def group_words_into_lines(words):
    """
    Group words into lines based on their vertical position.
    Words with similar Y coordinates (within tolerance) are considered on the same line.
    """
    if not words:
        return []
    
    lines = []
    
    # Sort words by top position first to process them top-to-bottom
    sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    
    for word in sorted_words:
        placed = False
        
        # Try to find an existing line this word belongs to
        for line in lines:
            # Use top position for more consistent grouping
            if abs(word["top"] - line["top"]) <= Y_TOLERANCE:
                line["words"].append(word)
                # Update line boundaries
                line["top"] = min(line["top"], word["top"])
                line["bottom"] = max(line["bottom"], word["bottom"])
                line["x0"] = min(line["x0"], word["x0"])
                line["x1"] = max(line["x1"], word["x1"])
                placed = True
                break
        
        # If word doesn't fit in any existing line, create a new line
        if not placed:
            lines.append({
                "top": word["top"],
                "bottom": word["bottom"],
                "x0": word["x0"],
                "x1": word["x1"],
                "words": [word]
            })
    
    # Sort words within each line from left to right
    for line in lines:
        line["words"].sort(key=lambda w: w["x0"])
    
    # Sort lines from top to bottom
    lines.sort(key=lambda line: line["top"])
    
    return lines

def extract_page_with_layout(page):
    """
    Extract text from a page while preserving the visual layout.
    Groups words into lines and sorts them properly for natural reading order.
    """
    # Extract words with their position information
    words = page.extract_words(extra_attrs=["x0", "x1", "top", "bottom"])
    
    if not words:
        print("No text found on this page.")
        return
    
    # Group words into lines based on their vertical position
    lines = group_words_into_lines(words)
    
    # Print each line
    for line in lines:
        text = " ".join(word["text"] for word in line["words"])
        if text.strip():  # Only print non-empty lines
            print(text)

def read_pdf_with_layout(pdf_path):
    """
    Read a PDF file and extract text with proper layout preservation.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"File: {os.path.basename(pdf_path)}")
            print(f"Total pages: {num_pages}")
            
            for i, page in enumerate(pdf.pages, start=1):
                print(f"\n--- Page {i} ---")
                extract_page_with_layout(page)
                
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")

def main():
    """
    Process all PDF files in the input directory.
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
        print("READING PDF WITH LAYOUT AWARENESS")
        read_pdf_with_layout(pdf_path)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()