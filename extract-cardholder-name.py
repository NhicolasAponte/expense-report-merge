import os
import re
from PyPDF2 import PdfReader

# --- Global Variables ---
INPUT_DIR = r"C:\Users\nflores\Desktop\temp\umb"  # Hard-coded directory path
CARDHOLDER_PATTERNS = [
    r'Cardholder Name:\s*([A-Za-z\s]+)',
]
NOT_FOUND = "UNKNOWN_CARDHOLDER"

def list_pdf_files(directory):
    """Returns a list of PDF files in the specified directory."""
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []
    return [file for file in os.listdir(directory) if file.lower().endswith('.pdf')]

def extract_text_from_pdf(pdf_path):
    """Extracts text from all pages of a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def find_cardholder_name(text):
    """Searches for cardholder name in the PDF text using predefined patterns."""
    # print("  Searching for cardholder name...")
    # print("XXXXX")
    # print(" ")
    # print(text)
    # print(" ")
    # print("XXXXX")
    for pattern in CARDHOLDER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name (remove extra spaces, validate)
            cleaned_name = re.sub(r'\s+', ' ', name).strip()
            if len(cleaned_name) > 1 and cleaned_name.replace(' ', '').isalpha():
                return cleaned_name
    return NOT_FOUND

def sanitize_filename(name):
    """Sanitizes a name for use in a filename by removing invalid characters."""
    # Remove spaces and remove invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.replace(' ', '')
    return sanitized.lower()

def generate_new_filename(original_filename, cardholder_name):
    """Generates a new filename with the cardholder name."""
    name, ext = os.path.splitext(original_filename)
    sanitized_name = sanitize_filename(cardholder_name)
    return f"{sanitized_name}_{"st"}{ext}"

def rename_file(old_path, new_filename):
    """Renames a file, handling conflicts by appending a number."""
    directory = os.path.dirname(old_path)
    new_path = os.path.join(directory, new_filename)
    
    # Handle filename conflicts
    counter = 1
    base_name, ext = os.path.splitext(new_filename)
    while os.path.exists(new_path):
        conflicted_filename = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(directory, conflicted_filename)
        counter += 1
    
    try:
        os.rename(old_path, new_path)
        print(f"Renamed: {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
        return True
    except Exception as e:
        print(f"Error renaming {old_path}: {e}")
        return False

def process_single_pdf(pdf_path):
    """Processes a single PDF file to extract cardholder name and rename the file."""
    print(f"Processing: {os.path.basename(pdf_path)}")
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"  No text found in {os.path.basename(pdf_path)}")
        return False
    
    # Find cardholder name
    cardholder_name = find_cardholder_name(text)
    if cardholder_name == NOT_FOUND:
        print(f"  No cardholder name found in {os.path.basename(pdf_path)}")
        return False
    
    print(f"  Found cardholder: {cardholder_name}")
    
    # Generate new filename and rename
    original_filename = os.path.basename(pdf_path)
    new_filename = generate_new_filename(original_filename, cardholder_name)
    
    return rename_file(pdf_path, new_filename)

def main():
    """Main function that processes all PDFs in the input directory."""
    print(f"Searching for PDFs in: {INPUT_DIR}")
    
    pdf_files = list_pdf_files(INPUT_DIR)
    if not pdf_files:
        print("No PDF files found.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    print("-" * 50)
    
    successful_renames = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        if process_single_pdf(pdf_path):
            successful_renames += 1
        print()  # Add blank line between files
    
    print("-" * 50)
    print(f"Successfully renamed {successful_renames} out of {len(pdf_files)} files")

if __name__ == "__main__":
    main()