from pathlib import Path 
import os 
from PyPDF2 import PdfMerger

#This script merges PDF files in a specified input folder and saves the merged file in an output folder.
# \\mhk-fs01\hive$\NetAdmin\Data\Nflores\Desktop\merge-pdfs 
# local input: C:\Users\nflores\Desktop\pdfs-to-merge 
# local output: C:\Users\nflores\Desktop\merged-pdfs 
input_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge")
output_folder = Path("C:/Users/nflores/Desktop/merged-pdfs")
output_folder.mkdir(exist_ok=True) 


def merge_pdfs(input_folder, output_folder):
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in the input folder")
        return 
    
    merger = PdfMerger()
    for pdf_file in pdf_files: 
        print(f"merging {pdf_file.name}")
        merger.append(pdf_file)

    output_file = output_folder / "merged.pdf"
    merger.write(output_file)
    merger.close()
    print(f"Merged PDF saved as {output_file}")

def main():
    merge_pdfs(input_folder, output_folder)

if __name__ == "__main__":
    main()
    print("PDF merging completed.")