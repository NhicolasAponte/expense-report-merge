import os
import ocrmypdf
from datetime import datetime
from config import LOCAL_DESKTOP_TEMP

INPUT_DIR = LOCAL_DESKTOP_TEMP
OUTPUT_DIR = LOCAL_DESKTOP_TEMP

def get_new_filename(original_name, suffix="_ocr"):
    name, ext = os.path.splitext(original_name)
    now = datetime.now()
    timestamp = now.strftime("%m%d_%H%M")
    return f"{name}{suffix}_{timestamp}{ext}"

def ocr_pdf(pdf_path):
    "APPLYING OCR TO PDF"
    output_filename = get_new_filename(os.path.basename(pdf_path), suffix="_ocr")
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    ocrmypdf.ocr(
        pdf_path,
        output_path,
        rotate_pages=True,
        deskew=True,
        progress_bar=True,
        force_ocr=True,
        skip_text=True
    )

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print("READING ORIGINAL PDF")
            ocr_pdf(pdf_path)

if __name__ == "__main__":
    main()