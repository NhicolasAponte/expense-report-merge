import os
import re
import csv
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from config import LOCAL_DESKTOP_TEMP

# --- Hard-coded global variables for input and output directories ---
INPUT_DIR = LOCAL_DESKTOP_TEMP
OUTPUT_DIR = os.path.join(INPUT_DIR, "ready-for-invoicing")
INVOICE_LIST = []
NOT_FOUND = "NOT_FOUND"
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")

def list_pdfs(directory):
    return [file for file in os.listdir(directory) if file.lower().endswith('.pdf')]

def get_timestamped_subdir(base_dir):
    subdir_path = os.path.join(base_dir, TIMESTAMP)
    os.makedirs(subdir_path, exist_ok=True)
    return subdir_path

def get_invoice_number_from_line(line):
    
    invoice_number = NOT_FOUND
    match = re.search(r'#\s*[mM](.{6})', line)
    if match:
        invoice_number = match.group(1).strip()
    else:
        first_line_lower = line.lower()
        match_alt = re.search(r'm(\d{6})', first_line_lower)
        if match_alt:
            invoice_number = match_alt.group(1)
        else:
            match_digits = re.search(r'#\s*(\d{6})', line)
            if match_digits:
                invoice_number = match_digits.group(1)
    if invoice_number != NOT_FOUND and invoice_number not in INVOICE_LIST:
        INVOICE_LIST.append(invoice_number)
    return invoice_number 

def split_pdf_by_page(pdf_path, output_dir):
    try: 
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        if num_pages == 0:
            print(f"No pages found in {pdf_path}. Skipping.")
            return
        for i, page in enumerate(reader.pages, start=1):
            
            page_text = page.extract_text() or ""
            first_line = page_text.strip().split('\n')[0] if page_text.strip() else ""
            invoice_number = get_invoice_number_from_line(first_line)
            file_name = ""
            if invoice_number == NOT_FOUND:
                file_name = f"page_{i:03d}_no_invoice.pdf"
            else:
                file_name = f"{invoice_number}.pdf"
            output_path = os.path.join(output_dir, file_name)
            writer = PdfWriter()
            writer.add_page(page)
            with open(output_path, "wb") as output_pdf:
                writer.write(output_pdf)
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

def get_csv_filename(prefix="invoice_batch"):
    return f"{prefix}_{TIMESTAMP}.csv"

def write_csv_to_ready_for_invoicing(data, filename=None):
    # Get the path to the user's Desktop/ready-for-invoicing
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_dir = os.path.join(desktop_path, "ready-for-invoicing")
    os.makedirs(target_dir, exist_ok=True)  # Create the directory if it doesn't exist
    if filename is None:
        filename = get_csv_filename()
    output_path = os.path.join(target_dir, filename)
    with open(output_path, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)
    print(f"Cleaned invoice list exported to {output_path}")
    

if __name__ == "__main__":
    split_output_dir = get_timestamped_subdir(OUTPUT_DIR)
    pdf_files = list_pdfs(INPUT_DIR)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        print()
        split_pdf_by_page(pdf_path, split_output_dir)
    write_csv_to_ready_for_invoicing(INVOICE_LIST)
    print(f"Total unique invoice numbers extracted: {len(INVOICE_LIST)}")