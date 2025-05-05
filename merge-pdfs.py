from pathlib import Path
import os
from PyPDF2 import PdfReader, PdfWriter
import shutil

# This script merges PDF files in a specified input folder and saves the merged file in an output folder.
# \\mhk-fs01\hive$\NetAdmin\Data\Nflores\Desktop\merge-pdfs
# local input: C:\Users\nflores\Desktop\pdfs-to-merge
# local output: C:\Users\nflores\Desktop\merged-pdfs
input_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge")
output_folder = Path("C:/Users/nflores/Desktop/merged-pdfs")
processed_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge/processed")
output_folder.mkdir(exist_ok=True)
processed_folder.mkdir(exist_ok=True)


def merge_pdfs_without_blank_pages(input_folder, output_folder, processed_folder):
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in the input folder")
        return

    writer = PdfWriter()
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}")
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            if page.extract_text().strip():  # Check if the page has text
                writer.add_page(page)
            else:
                print(f"Blank page removed from {pdf_file.name}")

        # Move the processed file to the processed folder
        processed_path = processed_folder / pdf_file.name
        shutil.move(str(pdf_file), str(processed_path))
        print(f"Moved {pdf_file.name} to {processed_path}")

    output_file = output_folder / "merged_no_blanks.pdf"
    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"Merged PDF without blank pages saved as {output_file}")


def main():
    merge_pdfs_without_blank_pages(input_folder, output_folder, processed_folder)


if __name__ == "__main__":
    main()
    print("PDF merging, blank page removal, and file processing completed.")