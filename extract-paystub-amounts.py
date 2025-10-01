import os
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader

# Reusable path variables
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
INPUT_FILE = os.path.join(TEST_FILES_DIR, "All_22_Paystubs.pdf")
OUTPUT_CSV = os.path.join(TEST_FILES_DIR, "earnings.csv")

def extract_earnings_from_page(text, filename, page_num):
    """Extract earnings data from a single page of text"""
    lines = text.split('\n')
    
    # Initialize result list for this page
    page_earnings = []
    
    # Find EARNINGS section
    earnings_start = -1
    earnings_end = -1
    
    for i, line in enumerate(lines):
        if "EARNINGS" in line and earnings_start == -1:
            earnings_start = i
        elif earnings_start != -1 and ("TAX DEDUCTIONS" in line or "DEDUCTIONS" in line):
            earnings_end = i
            break
    
    if earnings_start == -1:
        print(f"   ⚠️  Page {page_num}: No EARNINGS section found")
        return []
    
    earnings_end = earnings_end if earnings_end > 0 else len(lines)
    
    # Extract earnings categories
    earnings_categories = []
    for i in range(earnings_start + 1, earnings_end):
        line = lines[i].strip()
        if line and not line.startswith('***') and not line.startswith('���'):
            earnings_categories.append(line)
    
    if not earnings_categories:
        print(f"   ⚠️  Page {page_num}: No earnings categories found")
        return []
    
    print(f"   📋 Page {page_num}: Found {len(earnings_categories)} categories: {earnings_categories}")
    
    # Find the Hours column data
    hours_data = []
    hours_line_idx = -1
    
    # Look for "Hours" header
    for i, line in enumerate(lines):
        if line.strip() == "Hours":
            hours_line_idx = i
            break
    
    if hours_line_idx >= 0:
        # Collect hours data from the lines following the Hours header
        for i in range(hours_line_idx + 1, min(hours_line_idx + 1 + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            # Extract decimal number from the line
            hour_match = re.search(r'\d+\.\d+', line)
            if hour_match:
                hours_data.append(hour_match.group())
            else:
                hours_data.append("0.00")
    
    # Find Amount and YTD data
    amount_ytd_data = []
    amount_line_idx = -1
    ytd_line_idx = -1
    
    # Look for "Amount" and "YTD" headers
    for i, line in enumerate(lines):
        if "Amount" in line and amount_line_idx == -1:
            amount_line_idx = i
        if line.strip() == "YTD" and ytd_line_idx == -1:
            ytd_line_idx = i
    
    # Extract Amount and YTD data pairs
    if ytd_line_idx >= 0:
        # The data starts after the YTD header
        data_start = ytd_line_idx + 1
        for i in range(data_start, min(data_start + len(earnings_categories), len(lines))):
            line = lines[i].strip()
            # Extract two decimal numbers from each line (Amount and YTD)
            numbers = re.findall(r'\d+(?:,\d{3})*\.?\d*', line)
            if len(numbers) >= 2:
                # Remove commas for proper decimal conversion
                amount = numbers[0].replace(',', '')
                ytd = numbers[1].replace(',', '')
                amount_ytd_data.append((amount, ytd))
            else:
                amount_ytd_data.append(("0.00", "0.00"))
    
    # Match categories with their data
    for i, category in enumerate(earnings_categories):
        hours = hours_data[i] if i < len(hours_data) else "0.00"
        amount, ytd = amount_ytd_data[i] if i < len(amount_ytd_data) else ("0.00", "0.00")
        
        earnings_record = {
            'filename': filename,
            'page_number': page_num,
            'category': category,
            'hours': hours,
            'amount': amount,
            'ytd': ytd
        }
        
        page_earnings.append(earnings_record)
        print(f"   💰 {category}: Hours={hours}, Amount={amount}, YTD={ytd}")
    
    return page_earnings

def extract_all_earnings(pdf_path):
    """Extract earnings data from all pages of the PDF"""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return []
        
        filename = os.path.basename(pdf_path)
        all_earnings = []
        
        print(f"📄 Processing {filename} ({len(reader.pages)} pages)")
        
        # Process each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                print(f"   ⚠️  Page {page_num}: No text found")
                continue
            
            # Extract earnings from this page
            page_earnings = extract_earnings_from_page(text, filename, page_num)
            
            if page_earnings:
                all_earnings.extend(page_earnings)
                print(f"   ✅ Page {page_num}: {len(page_earnings)} earnings records extracted")
            else:
                print(f"   ⚠️  Page {page_num}: No earnings data found")
        
        return all_earnings
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
        return []

def export_earnings_to_csv(earnings_data, output_file):
    """Export earnings data to CSV file"""
    if not earnings_data:
        print("❌ No earnings data to export.")
        return
    
    # CSV headers
    headers = ['filename', 'page_number', 'category', 'hours', 'amount', 'ytd']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for record in earnings_data:
                writer.writerow(record)
        
        print(f"✅ Earnings data exported to: {output_file}")
        print(f"📊 Records exported: {len(earnings_data)}")
        
        # Show summary statistics
        categories = set(record['category'] for record in earnings_data)
        pages = set(record['page_number'] for record in earnings_data)
        
        print(f"📈 Summary:")
        print(f"   Pages processed: {len(pages)}")
        print(f"   Unique categories: {len(categories)}")
        print(f"   Categories found: {sorted(categories)}")
        
    except Exception as e:
        print(f"❌ Error writing CSV file: {str(e)}")

def main():
    """Main function to process the PDF and export earnings data"""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
    
    print(f"🔍 Extracting earnings data from: {INPUT_FILE}")
    
    # Extract all earnings data
    earnings_data = extract_all_earnings(INPUT_FILE)
    
    if earnings_data:
        # Export to CSV
        export_earnings_to_csv(earnings_data, OUTPUT_CSV)
        print(f"\n🎉 Processing complete!")
        print(f"   📁 CSV file location: {OUTPUT_CSV}")
    else:
        print("❌ No earnings data found to export.")

if __name__ == "__main__":
    main()
