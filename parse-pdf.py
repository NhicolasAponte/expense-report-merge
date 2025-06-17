import os
import sys
import re
from PyPDF2 import PdfReader, PdfWriter

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
    return invoice_number

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
            if invoice_number != current_invoice:
                # Save the previous invoice PDF if exists
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
    if len(sys.argv) != 2:
        print("Usage: python parse-pdf.py <directory>")
        sys.exit(1)
    directory = sys.argv[1]
    pdf_files = list_pdfs(directory)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        # print(f"--- {pdf_file} ---")
        print()
        # Call split_invoices for each file
        split_invoices(pdf_path, os.path.join(directory, "split-invoices"))