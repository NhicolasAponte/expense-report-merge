import os
from io import BytesIO
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import ocrmypdf
from config import LOCAL_INPUT_DIR, LOCAL_OUTPUT_DIR

INPUT_DIR = LOCAL_INPUT_DIR
OUTPUT_DIR = LOCAL_OUTPUT_DIR

def get_new_filename(original_name, suffix="_ocr"):
    name, ext = os.path.splitext(original_name)
    now = datetime.now()
    timestamp = now.strftime("%m%d_%H%M")
    return f"{name}{suffix}_{timestamp}{ext}"

def flip_pdf_in_memory(input_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(180)
        writer.add_page(page)
    mem_pdf = BytesIO()
    writer.write(mem_pdf)
    mem_pdf.seek(0)
    return mem_pdf

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            input_pdf = os.path.join(INPUT_DIR, filename)
            print(f"Flipping and OCR: {filename}")
            flipped_pdf = flip_pdf_in_memory(input_pdf)
            output_pdf = os.path.join(OUTPUT_DIR, get_new_filename(filename, suffix="_ocr"))
            ocrmypdf.ocr(
                flipped_pdf,
                output_pdf,
                rotate_pages=True,
                deskew=True,
                progress_bar=True,
            )
    print("Done flipping and OCR'ing all PDFs.")

if __name__ == "__main__":
    main()