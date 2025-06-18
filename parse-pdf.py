import os
import re
import csv
from PyPDF2 import PdfReader, PdfWriter

# --- Hard-coded global variables for input and output directories ---
INPUT_DIR = r"C:\Users\nflores\Desktop\temp"
OUTPUT_DIR = os.path.join(INPUT_DIR, "ready-for-invoicing")
INVOICE_LIST = []

def list_pdfs(directory):
    return [file for file in os.listdir(directory) if file.lower().endswith('.pdf')]

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        page_first_lines = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text
            # Get the first line of the page
            first_line = page_text.strip().split('\n')[0] if page_text.strip() else ""
            page_first_lines.append(first_line)
        num_pages = len(reader.pages)
        return text, num_pages, page_first_lines
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return "", 0, []

def get_invoice_number_from_line(line):
    invoice_number = "Not found"
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
    if invoice_number != "Not found" and invoice_number not in INVOICE_LIST:
        INVOICE_LIST.append(invoice_number)

    return invoice_number 

def write_csv_to_ready_for_invoicing(data, filename="cleaned_invoices.csv"):
    # Get the path to the user's Desktop/ready-for-invoicing
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_dir = os.path.join(desktop_path, "ready-for-invoicing")
    os.makedirs(target_dir, exist_ok=True)  # Create the directory if it doesn't exist
    output_path = os.path.join(target_dir, filename)
    with open(output_path, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)
    print(f"Cleaned invoice list exported to {output_path}")

def split_invoices(pdf_path, output_dir):
    try:
        reader = PdfReader(pdf_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        current_writer = None
        current_invoice = None
        page_indices = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            first_line = page_text.strip().split('\n')[0] if page_text.strip() else ""
            invoice_number = get_invoice_number_from_line(first_line)
            # If a new invoice number is found, save the previous invoice PDF
            if invoice_number != "Not found" and invoice_number != current_invoice:
                if current_writer and current_invoice and page_indices:
                    output_path = os.path.join(
                        output_dir,
                        f"{current_invoice}.pdf"
                    )
                    with open(output_path, "wb") as out_f:
                        current_writer.write(out_f)
                # Start a new writer for the new invoice
                current_writer = PdfWriter()
                current_invoice = invoice_number
                page_indices = []
            # If no invoice number is found, treat as attachment for current invoice
            if current_writer is None and invoice_number == "Not found":
                # If the first page(s) are attachments with no invoice number, skip until we find an invoice number
                continue
            if current_writer is not None:
                current_writer.add_page(page)
                page_indices.append(i)
        # Save the last invoice PDF
        if current_writer and current_invoice and page_indices:
            output_path = os.path.join(
                output_dir,
                f"{current_invoice}.pdf"
            )
            with open(output_path, "wb") as out_f:
                current_writer.write(out_f)
        print(f"Split invoices for {os.path.basename(pdf_path)} saved to {output_dir}")
    except Exception as e:
        print(f"Error splitting {pdf_path}: {e}")


if __name__ == "__main__":
    pdf_files = list_pdfs(INPUT_DIR)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        print()
        split_invoices(pdf_path, OUTPUT_DIR)
    write_csv_to_ready_for_invoicing(INVOICE_LIST)
    print(f"Total unique invoice numbers extracted: {len(INVOICE_LIST)}")