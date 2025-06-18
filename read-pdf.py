import os
from PyPDF2 import PdfReader
import ocrmypdf

INPUT_DIR = r"C:\Users\nflores\Desktop\temp"  # Change as needed
OUTPUT_DIR = os.path.join(INPUT_DIR, "ocr-pdfs")

def read_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    print(f"File: {os.path.basename(pdf_path)}")
    print(f"Total pages: {num_pages}")
    for i, page in enumerate(reader.pages, start=1):
        print(f"\n--- Page {i} ---")
        text = page.extract_text() or ""
        print(text.strip())

def ocr_pdf(pdf_path):
    "APPLYING OCR TO PDF" 
    ocrmypdf.ocr(
        pdf_path,
        os.path.join(OUTPUT_DIR, os.path.basename(pdf_path)),
        rotate_pages=True,
        deskew=True,
        progress_bar=True,
        # force_ocr=True,
        # skip_text=True
    )

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print("READING ORIGINAL PDF")
            read_pdf(pdf_path)
            ocr_pdf(pdf_path)
    # for filename in os.listdir(OUTPUT_DIR):
    #     if filename.lower().endswith(".pdf"):
    #         print("READING OCR PDF")
    #         pdf_path = os.path.join(OUTPUT_DIR, filename)
    #         read_pdf(pdf_path)

if __name__ == "__main__":
    main()