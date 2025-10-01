import os
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_DIR = TEST_FILES_DIR
OUTPUT_CSV = os.path.join(TEST_FILES_DIR, "paystub_data.csv")

def extract_paystub_data(pdf_path):
    """Extract employee data from paystub PDF"""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return None
        
        # Extract text from first page
        text = reader.pages[0].extract_text() or ""
        if not text.strip():
            return None
        
        # Initialize data dictionary
        data = {
            'filename': os.path.basename(pdf_path),
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
        
        # Extract the actual pay rate (the number that appears after Pay Rate***)
        pay_rate_pattern = r'Pay Rate\*\*\*-\*\*-(\d+)'
        pay_rate_match = re.search(pay_rate_pattern, text)
        if pay_rate_match:
            data['pay_rate'] = pay_rate_match.group(1).strip()
        
        # Extract stub number (the code between Stub Number and Hours)
        stub_pattern = r'Stub Number([A-Z0-9]+)Hours'
        stub_match = re.search(stub_pattern, text)
        if stub_match:
            data['stub_number'] = stub_match.group(1).strip()
        
        # Extract employee number from the stub number field (seems to be embedded)
        # The actual employee number appears to be the alphanumeric after "00-"
        emp_pattern = r'YTD([0-9]{2}-[A-Z]+)\*\*\*'
        emp_match = re.search(emp_pattern, text)
        if emp_match:
            data['employee_number'] = emp_match.group(1).strip()
        
        return data
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None

def export_to_csv(data_list, output_file):
    """Export extracted data to CSV file"""
    if not data_list:
        print("No data to export.")
        return
    
    # CSV headers
    headers = ['filename', 'employee_name', 'employee_number', 'pay_rate', 'stub_number', 'processed_date']
    
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
    
    print(f"🔍 Processing PDFs in: {INPUT_DIR}")
    
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"📄 Processing: {filename}")
            
            data = extract_paystub_data(pdf_path)
            if data:
                extracted_data.append(data)
                processed_files += 1
                print(f"   ✅ Employee: {data['employee_name']}")
                print(f"   📋 Emp #: {data['employee_number']}")
                print(f"   💰 Pay Rate: {data['pay_rate']}")
                print(f"   🆔 Stub #: {data['stub_number']}")
            else:
                print(f"   ❌ Failed to extract data from {filename}")
            print()
    
    if extracted_data:
        export_to_csv(extracted_data, OUTPUT_CSV)
        print(f"\n📈 Summary:")
        print(f"   Files processed: {processed_files}")
        print(f"   CSV location: {OUTPUT_CSV}")
    else:
        print("❌ No paystub data found to export.")

if __name__ == "__main__":
    main()