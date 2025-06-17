import os
import sys
import re
import csv

def list_pdfs(directory):
    pdf_files = []
    for file in os.listdir(directory):
        if file.lower().endswith('.pdf'):
            pdf_files.append(file)
    return pdf_files

def clean_pdf_filename(filename):
    # Remove the file extension
    name, _ = os.path.splitext(filename)
    # Remove non-numeric characters
    cleaned = re.sub(r'\D', '', name)
    return cleaned

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get-invoice-list.py <directory>")
        sys.exit(1)
    directory = sys.argv[1]
    pdfs = list_pdfs(directory)
    cleaned_list = [clean_pdf_filename(pdf) for pdf in pdfs]
    write_csv_to_ready_for_invoicing(cleaned_list)