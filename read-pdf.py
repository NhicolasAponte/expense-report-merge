import os
from PyPDF2 import PdfReader
from datetime import datetime
from config import LOCAL_DESKTOP_TEMP

INPUT_DIR = LOCAL_DESKTOP_TEMP

def read_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    print(f"File: {os.path.basename(pdf_path)}")
    print(f"Total pages: {num_pages}")
    for i, page in enumerate(reader.pages, start=1):
        print(f"\n--- Page {i} ---")
        text = page.extract_text() or ""
        print(text.strip())

def main():
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print("READING ORIGINAL PDF")
            read_pdf(pdf_path)
            

if __name__ == "__main__":
    main()