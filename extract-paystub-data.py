import os
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_DIR = TEST_FILES_DIR
OUTPUT_CSV = os.path.join(TEST_FILES_DIR, "paystub_data.csv")

def extract_paystub_data_from_page(text, filename, page_num):
    """Extract employee data from a single page of text"""
    # Initialize data dictionary
    data = {
        'filename': filename,
        'page_number': page_num,
        'employee_name': '',
        'employee_number': '',
        'pay_rate': '',
        'stub_number': ''
    }
    
    # Extract employee name (appears between date and address)
    name_pattern = r'\d{1,2}/\d{1,2}/\d{4}([A-Za-z\s\.]+?)\d{4}\s+Tuttle'
    name_match = re.search(name_pattern, text)
    if name_match:
        data['employee_name'] = name_match.group(1).strip()
    
    # Extract pay rate (the decimal number after "HW")
    pay_rate_pattern = r'HW(\d+\.\d+)'
    pay_rate_match = re.search(pay_rate_pattern, text)
    if pay_rate_match:
        data['pay_rate'] = pay_rate_match.group(1).strip()
    
    # Extract stub number (the code between "Stub Number" and "Hours")
    stub_pattern = r'Stub Number([A-Z0-9]+)Hours'
    stub_match = re.search(stub_pattern, text)
    if stub_match:
        data['stub_number'] = stub_match.group(1).strip()
    
    # Extract employee number (the code after "YTD" and before "***")
    emp_pattern = r'YTD([0-9]{2}-[A-Z]+)\*\*\*'
    emp_match = re.search(emp_pattern, text)
    if emp_match:
        data['employee_number'] = emp_match.group(1).strip()
    
    return data

def extract_paystub_data(pdf_path):
    """Extract employee data from all pages of paystub PDF"""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return []
        
        filename = os.path.basename(pdf_path)
        extracted_pages = []
        
        # Process each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                print(f"   ⚠️  Page {page_num}: No text found")
                continue
            
            # Extract data from this page
            page_data = extract_paystub_data_from_page(text, filename, page_num)
            
            # Only add if we found at least some data
            if any([page_data['employee_name'], page_data['employee_number'], 
                   page_data['pay_rate'], page_data['stub_number']]):
                extracted_pages.append(page_data)
                print(f"   ✅ Page {page_num}: Data extracted")
            else:
                print(f"   ⚠️  Page {page_num}: No paystub data found")
        
        return extracted_pages
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return []

def export_to_csv(data_list, output_file):
    """Export extracted data to CSV file"""
    if not data_list:
        print("No data to export.")
        return
    
    # CSV headers (now includes page_number)
    headers = ['filename', 'page_number', 'employee_name', 'employee_number', 'pay_rate', 'stub_number', 'processed_date']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for data in data_list:
                # Add processing timestamp
                data['processed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow(data)
        
        print(f"✅ Data exported to: {output_file}")
        print(f"📊 Records exported: {len(data_list)}")
        
    except Exception as e:
        print(f"❌ Error writing CSV file: {str(e)}")

def main():
    """Main function to process all PDFs and export data"""
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Input directory not found: {INPUT_DIR}")
        return
    
    extracted_data = []
    processed_files = 0
    total_pages = 0
    
    print(f"🔍 Processing PDFs in: {INPUT_DIR}")
    
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"📄 Processing: {filename}")
            
            # Get data from all pages
            page_data_list = extract_paystub_data(pdf_path)
            
            if page_data_list:
                # Add all page data to our master list
                extracted_data.extend(page_data_list)
                processed_files += 1
                total_pages += len(page_data_list)
                
                print(f"   📊 Pages processed: {len(page_data_list)}")
                
                # Show summary for each page
                for page_data in page_data_list:
                    print(f"   📄 Page {page_data['page_number']}:")
                    print(f"      👤 Employee: {page_data['employee_name']}")
                    print(f"      📋 Emp #: {page_data['employee_number']}")
                    print(f"      💰 Pay Rate: {page_data['pay_rate']}")
                    print(f"      🆔 Stub #: {page_data['stub_number']}")
            else:
                print(f"   ❌ Failed to extract data from {filename}")
            print()
    
    if extracted_data:
        export_to_csv(extracted_data, OUTPUT_CSV)
        print(f"\n📈 Summary:")
        print(f"   Files processed: {processed_files}")
        print(f"   Total pages processed: {total_pages}")
        print(f"   Total records: {len(extracted_data)}")
        print(f"   CSV location: {OUTPUT_CSV}")
    else:
        print("❌ No paystub data found to export.")

if __name__ == "__main__":
    main()