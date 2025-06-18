import os
from PyPDF2 import PdfReader, PdfWriter

INPUT_DIR = r"C:\Users\nflores\Desktop\temp"  # Change as needed
OUTPUT_DIR = os.path.join(INPUT_DIR, "flipped")

def flip_pdf_pages(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(180)
        writer.add_page(page)
    with open(output_pdf_path, "wb") as out_f:
        writer.write(out_f)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            input_pdf = os.path.join(INPUT_DIR, filename)
            name, ext = os.path.splitext(filename)
            output_pdf = os.path.join(OUTPUT_DIR, f"{name}_flipped{ext}")
            print(f"Flipping: {filename}")
            flip_pdf_pages(input_pdf, output_pdf)
    print("Done flipping all PDFs.")

if __name__ == "__main__":
    main()