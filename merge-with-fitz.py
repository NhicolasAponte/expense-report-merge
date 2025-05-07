from pathlib import Path
import os
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import fitz  # PyMuPDF 
import shutil 

# Define folders

# local folders 
# input_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge")
output_folder = Path("C:/Users/nflores/Desktop/merged-pdfs")
# ap folders 
# input_folder  
input_folder = Path("C:/Users/nflores/OneDrive - Manko Window Systems, Inc/credit_card_reports")
ap_input_folder = Path("//mws-doclink/SmartCapture/Input Folders/AP Invoice CREDIT CARD")


processed_folder = Path("C:/Users/nflores/Desktop/pdfs-to-merge/processed")
output_folder.mkdir(exist_ok=True)
processed_folder.mkdir(exist_ok=True)

def get_base_names(folder):
    """Extracts base names (e.g., 'JohnDoe') from files like 'JohnDoe_ReportType.pdf'."""
    print("Getting base names from folder...")
    names = set()
    for file in folder.glob("*.pdf"):
        parts = file.stem.rsplit("_", 1)
        if len(parts) == 2:
            names.add(parts[0])
    return names

def move_to_processed(merged_files):
    """Moves the processed PDF to the processed folder."""
    print(" ")
    print("Moving processed files to the processed folder...")
    count = 0
    if not processed_folder.exists():
        processed_folder.mkdir(parents=True, exist_ok=True)
    for file in merged_files:
        if file.exists():
            count += 1
            shutil.move(str(file), str(processed_folder / file.name))
            print(f"Moved {file.name} to processed folder.")
    print(f"Moved {count} files to the processed folder.")

def move_to_ap_input_folder():
    """Moves the processed PDF to the AP Input Folder."""
    print(" ")
    print("Moving processed files to the AP Input Folder...")

    if not ap_input_folder.exists():
        ap_input_folder.mkdir(parents=True, exist_ok=True)
    for file in output_folder.glob("*.pdf"):
        shutil.move(str(file), str(ap_input_folder / file.name))
        print(f"Moved {file.name} to AP Input Folder.")

def remove_last_page(pdf_path):
    """Removes the last page of a PDF and saves a cleaned version."""
    print(" ")
    print("Removing last page from PDF...")

    doc = fitz.open(pdf_path)
    if doc.page_count > 0:
        doc.delete_page(-1)
    modified_path = pdf_path.with_stem(pdf_path.stem + "_removed_last_page")
    doc.save(modified_path)
    doc.close()
    return modified_path

def remove_services_page(pdf_path):
    """Removes the 'Services' page from a PDF and saves a cleaned version."""
    print(" ")
    print("Removing 'Services' page from PDF...")

    doc = fitz.open(pdf_path)

    if len(doc) > 1:
        last_page = doc[-1]
        text = last_page.get_text()
        if "Do you need to dispute a transaction?" in text:
            doc.delete_page(-1)
        modified_path = pdf_path.with_stem(pdf_path.stem + "_removed_services") 
        doc.save(modified_path)
        doc.close()
        return modified_path
    
    return pdf_path  # Return original if no modification was made 


def is_blank(page):
    """Heuristic to detect if a page is blank using text content and image count."""
    text = page.get_text()

    print("xxxxxxxxxxxxxxxxxxxxxxxx")
    print(f"Extracted text: {text}")  # Debugging line 
    print("---------------------")

    images = page.get_images()
    print(f"Number of images: {len(images)}")  # Debugging line
    print("---------------------")

    return not text.strip() and not images

def remove_blank_pages(pdf_path):
    """Removes blank pages from a PDF and saves a cleaned version."""
    doc = fitz.open(pdf_path)
    non_blank_doc = fitz.open()
    for page in doc:
        if not is_blank(page):
            non_blank_doc.insert_pdf(doc, from_page=page.number, to_page=page.number)
    clean_path = pdf_path.with_stem(pdf_path.stem + "_cleaned")
    non_blank_doc.save(clean_path)
    return clean_path

def process_statement(pdf_path):
    """Processes the statement PDF to remove the last page."""
    print(" ")
    print("Processing statement PDF...")


    modified_path = remove_last_page(pdf_path) 
    cleaned_path = remove_services_page(modified_path)
    os.remove(modified_path)  # Remove the intermediate file
    # move original file to processed folder 
    # implementation here 
    return cleaned_path

def process_expense(pdf_path):
    """Processes the expense PDF to remove blank pages."""
    print(" ")
    print("Processing expense PDF...")
    
    doc = fitz.open(pdf_path)

    modified_path = pdf_path.with_stem(pdf_path.stem + "_working_copy")

    doc.save(modified_path)
    doc.close()

    return modified_path

def process_transactions(pdf_path):
    """Processes the transactions PDF to remove blank pages."""
    print(" ")
    print("Processing transactions PDF...")
    cleaned_path = remove_last_page(pdf_path)
    return cleaned_path

def has_all_required_files(name, folder):
    """Checks if all required files for a cardholder exist."""
    required_files = [
        folder / f"{name}_statement.pdf",
        folder / f"{name}_expense.pdf",
        folder / f"{name}_transactions.pdf"
    ]
    for file in required_files:
        if not file.exists():
            print(f"Missing required file: {file}")
            return False
    return True

# Process each cardholder
def process_pdfs():
    for name in get_base_names(input_folder):
        print(" ")
        print("XXXXXXXXXXXXXXXXX")
        print(f"Processing reports for {name}...")
        print(" ")

        if not has_all_required_files(name, input_folder):
            print(f"Skipping {name} due to missing files.")
            continue

        files_to_merge = [
            input_folder / f"{name}_statement.pdf",
            input_folder / f"{name}_expense.pdf",
            input_folder / f"{name}_transactions.pdf"
        ]
        
        # cleaned_files = [remove_blank_pages(f) for f in files_to_merge if f.exists()]
        
        cleaned_files = [
            process_statement(input_folder / f"{name}_statement.pdf"),
            process_expense(input_folder / f"{name}_expense.pdf"),
            process_transactions(input_folder / f"{name}_transactions.pdf")
        ]

        merger = PdfMerger()
        for f in cleaned_files:
            merger.append(str(f))
        merged_output = output_folder / f"{name}_report.pdf"
        merger.write(merged_output)
        merger.close()

        # Optionally remove temporary cleaned files
        for f in cleaned_files:
            os.remove(f)

        # move_to_processed(files_to_merge)
        print(f"Processed and merged reports for {name}.")

def main():
    process_pdfs()
    move_to_ap_input_folder()

if __name__ == "__main__":
    main() 
    print("All reports merged and moved to AP Input Folder.") 

"""
Moved altenhofen_report.pdf to AP Input Folder.
Moved bahner_report.pdf to AP Input Folder.
Moved beckman_report.pdf to AP Input Folder.
Moved beyer_report.pdf to AP Input Folder.
Moved bjones_report.pdf to AP Input Folder.
Moved burgess_report.pdf to AP Input Folder.
Moved campbell_report.pdf to AP Input Folder.
Moved cox_report.pdf to AP Input Folder.
Moved dix_report.pdf to AP Input Folder.
Moved ernst_report.pdf to AP Input Folder.
Moved frisbie_report.pdf to AP Input Folder.
Moved gehrer_report.pdf to AP Input Folder.
Moved gjones_report.pdf to AP Input Folder.
Moved hotel1_report.pdf to AP Input Folder.
Moved hotel3_report.pdf to AP Input Folder.
Moved howell_report.pdf to AP Input Folder.
Moved jenjones_report.pdf to AP Input Folder.
Moved jepsen_report.pdf to AP Input Folder.
Moved jerjones_report.pdf to AP Input Folder.
Moved kleinkauf_report.pdf to AP Input Folder.
Moved leuszler_report.pdf to AP Input Folder.
Moved lill_report.pdf to AP Input Folder.
Moved long_report.pdf to AP Input Folder.
Moved marts_report.pdf to AP Input Folder.
Moved mcguire_report.pdf to AP Input Folder.
Moved mhkpurchasing_report.pdf to AP Input Folder.
Moved modean_report.pdf to AP Input Folder.
Moved newman_report.pdf to AP Input Folder.
Moved ott_report.pdf to AP Input Folder.
Moved padgett_report.pdf to AP Input Folder.
Moved plummer_report.pdf to AP Input Folder.
Moved sjones_report.pdf to AP Input Folder.
Moved spiller_report.pdf to AP Input Folder.
Moved tesene_report.pdf to AP Input Folder.
Moved titterton_report.pdf to AP Input Folder.
Moved welty_report.pdf to AP Input Folder.
Moved wilkinson_report.pdf to AP Input Folder.
Moved yoder_report.pdf to AP Input Folder.
"""