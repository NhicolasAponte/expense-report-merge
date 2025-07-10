import os
import re
import csv
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from config import LOCAL_DESKTOP_TEMP

# this script is for testing edge cases 
# currently has logic for not skipping the first page if it 
# does not have an invoice number

# --- Hard-coded global variables for input and output directories ---
INPUT_DIR = LOCAL_DESKTOP_TEMP
OUTPUT_DIR = os.path.join(INPUT_DIR, "ready-for-invoicing")
INVOICE_LIST = []
NOT_FOUND = "NOT_FOUND"
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
FILENAME = ""

def list_pdfs(directory):
    return [file for file in os.listdir(directory) if file.lower().endswith('.pdf')]

def get_timestamped_subdir(base_dir, filename=None):
    if filename:
        name = filename.split('_')[0]
        base_name = name.split('-')[1]  # Remove file extension if present
        subdir_name = f"{base_name}_{TIMESTAMP}"
    else:
        subdir_name = TIMESTAMP
    subdir_path = os.path.join(base_dir, subdir_name)
    os.makedirs(subdir_path, exist_ok=True)
    return subdir_path

def get_invoice_number_from_page(page_text):
    invoice_number = NOT_FOUND
    patterns = [
        r'#\s*[mM](\d{6})',
        r'm(\d{6})',
        r'Work Order Number:\s*(\d{6})',
        r'Invoice #\s*(\d{6})',
        r'Invoice ID:\s*(\d{6})',
        # r'#\s*(\d{6})',
    ]
    # Search first line, then whole page
    lines = page_text.splitlines()
    for line in lines:
        if "quote" in line.lower():
            continue 
        normalized_line = re.sub(r'\s+', ' ', line).strip()
        for pattern in patterns:
            match = re.search(pattern, normalized_line, re.IGNORECASE)
            if match:
                invoice_number = match.group(1).strip()
                break
        if invoice_number != NOT_FOUND:
            break

    # Handle uniqueness in INVOICE_LIST
    if invoice_number != NOT_FOUND and invoice_number not in INVOICE_LIST:
        INVOICE_LIST.append(invoice_number)
    return invoice_number

def get_unique_filename(output_dir, base_filename):
    """
    Returns a unique file path in output_dir by appending _2, _3, etc. if needed.
    """
    name, ext = os.path.splitext(base_filename)
    candidate = base_filename
    counter = 2
    while os.path.exists(os.path.join(output_dir, candidate)):
        candidate = f"{name}_{counter}{ext}"
        counter += 1
    return candidate

def split_invoices(pdf_path, output_dir):
    try:
        reader = PdfReader(pdf_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        current_writer = None
        current_invoice = None
        page_indices = []
        pending_pages = []  # Store pages without invoice numbers
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            invoice_number = get_invoice_number_from_page(page_text)
            
            # case where invoice number is found and is different from the current one 
            if invoice_number != NOT_FOUND and invoice_number != current_invoice:
                # Save the current PDF if we have one
                if current_writer and page_indices:
                    # Use current_invoice or generate a placeholder name
                    invoice_name = current_invoice if current_invoice else f"UNKNOWN_{page_indices[0] + 1}"
                    base_filename = f"{page_indices[0] + 1}_{invoice_name}.pdf"
                    unique_filename = get_unique_filename(output_dir, base_filename)
                    output_path = os.path.join(output_dir, unique_filename)
                    with open(output_path, "wb") as out_f:
                        current_writer.write(out_f)
                
                # Start new PDF writer
                current_writer = PdfWriter()
                current_invoice = invoice_number
                page_indices = []
                
                # Add any pending pages (pages without invoice numbers) to this new invoice
                for pending_page in pending_pages:
                    current_writer.add_page(pending_page['page'])
                    page_indices.append(pending_page['index'])
                pending_pages = []
            
            # If no invoice number is found and we don't have a current writer, start a new one
            if current_writer is None and invoice_number == NOT_FOUND:
                # Store this page as pending until we find an invoice number
                pending_pages.append({'page': page, 'index': i})
                continue
            
            # Add the current page to the current writer
            if current_writer is not None:
                current_writer.add_page(page)
                page_indices.append(i)
        
        # Handle any remaining PDF at the end
        if current_writer and page_indices:
            invoice_name = current_invoice if current_invoice else f"UNKNOWN_{page_indices[0] + 1}"
            base_filename = f"{page_indices[0] + 1}_{invoice_name}.pdf"
            unique_filename = get_unique_filename(output_dir, base_filename)
            output_path = os.path.join(output_dir, unique_filename)
            with open(output_path, "wb") as out_f:
                current_writer.write(out_f)
        
        # Handle any remaining pending pages (pages at the end without invoice numbers)
        if pending_pages:
            final_writer = PdfWriter()
            final_indices = []
            for pending_page in pending_pages:
                final_writer.add_page(pending_page['page'])
                final_indices.append(pending_page['index'])
            
            base_filename = f"{final_indices[0] + 1}_UNKNOWN.pdf"
            unique_filename = get_unique_filename(output_dir, base_filename)
            output_path = os.path.join(output_dir, unique_filename)
            with open(output_path, "wb") as out_f:
                final_writer.write(out_f)
        
        print(f"Split invoices for {os.path.basename(pdf_path)} saved to {output_dir}")
    except Exception as e:
        print(f"Error splitting {pdf_path}: {e}")

def get_csv_filename(filename=None):
    filename = filename.split('_')[0] if filename else "invoice-batch"
    return f"{filename}_{TIMESTAMP}.csv"

def write_csv_to_ready_for_invoicing(data, filename=None):
    # Get the path to the user's Desktop/ready-for-invoicing
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_dir = os.path.join(desktop_path, "ready-for-invoicing")
    os.makedirs(target_dir, exist_ok=True)  # Create the directory if it doesn't exist
    if filename is None:
        filename = get_csv_filename(FILENAME)
    output_path = os.path.join(target_dir, filename)
    with open(output_path, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)
    print(f"Cleaned invoice list exported to {output_path}")

def move_original_to_output(pdf_path, output_dir):
    """
    Moves the original PDF to the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    base_filename = os.path.basename(pdf_path)
    output_path = os.path.join(output_dir, base_filename)
    if not os.path.exists(output_path):
        os.rename(pdf_path, output_path)
        print(f"Moved original PDF {base_filename} to {output_dir}")
    else:
        print(f"Original PDF {base_filename} already exists in {output_dir}, skipping move.")

if __name__ == "__main__":
    pdf_files = list_pdfs(INPUT_DIR)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        print()
        FILENAME = pdf_file 
        split_output_dir = get_timestamped_subdir(OUTPUT_DIR, FILENAME)
        split_invoices(pdf_path, split_output_dir)
        move_original_to_output(pdf_path, split_output_dir)
        write_csv_to_ready_for_invoicing(INVOICE_LIST)
        print(f"Total unique invoice numbers extracted: {len(INVOICE_LIST)}")