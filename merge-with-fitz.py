from pathlib import Path
import os
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import fitz  # PyMuPDF

# Define folders
input_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge")
output_folder = Path("C:/Users/nflores/Desktop/merged-pdfs")
processed_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge/processed")
output_folder.mkdir(exist_ok=True)
processed_folder.mkdir(exist_ok=True)

def is_blank(page):
    """Heuristic to detect if a page is blank using text content and image count."""
    text = page.get_text()

    print("---------------------")
    print(f"Extracted text: {text}")  # Debugging line 
    print("---------------------")

    images = page.get_images()
    return not text.strip() and not images

def remove_blank_pages(pdf_path):
    """Removes blank pages from a PDF and saves a cleaned version."""
    doc = fitz.open(pdf_path)
    non_blank_doc = fitz.open()
    for page in doc:
        if not is_blank(page):
            non_blank_doc.insert_pdf(doc, from_page=page.number, to_page=page.number)
    clean_path = pdf_path.with_stem(pdf_path.stem + "_cleaned")
    non_blank_doc.save(clean_path)
    return clean_path

def get_base_names(folder):
    """Extracts base names (e.g., 'JohnDoe') from files like 'JohnDoe_ReportType.pdf'."""
    names = set()
    for file in folder.glob("*.pdf"):
        parts = file.stem.rsplit("_", 1)
        if len(parts) == 2:
            names.add(parts[0])
    return names

# Process each cardholder
for name in get_base_names(input_folder):
    files_to_merge = [
        input_folder / f"{name}_statement.pdf",
        input_folder / f"{name}_expense.pdf",
        input_folder / f"{name}_codesummary.pdf"
    ]
    
    cleaned_files = [remove_blank_pages(f) for f in files_to_merge if f.exists()]
    
    merger = PdfMerger()
    for f in cleaned_files:
        merger.append(str(f))
    merged_output = output_folder / f"{name}_FinalReport.pdf"
    merger.write(merged_output)
    merger.close()

    # Optionally remove temporary cleaned files
    for f in cleaned_files:
        os.remove(f)

print("All reports merged and cleaned.")
