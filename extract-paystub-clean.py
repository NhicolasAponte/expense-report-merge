import os
import csv
import sys
import pdfplumber

# Add current directory to path to import our module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import using the actual filename with hyphens converted to underscores
import importlib.util
spec = importlib.util.spec_from_file_location("extract_paystub_structured", 
                                              os.path.join(current_dir, "extract-paystub-structured.py"))
extract_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_module)
PaystubExtractor = extract_module.PaystubExtractor

def create_earnings_csv(paystub_data_list, output_file="extracted_earnings.csv"):
    """Create a CSV file with all earnings data."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['employee_name', 'employee_number', 'pay_period_end', 'stub_number', 
                     'earning_type', 'hours', 'amount', 'ytd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for paystub in paystub_data_list:
            for earning in paystub.earnings:
                writer.writerow({
                    'employee_name': paystub.employee_name,
                    'employee_number': paystub.employee_number,
                    'pay_period_end': paystub.pay_period_end,
                    'stub_number': paystub.stub_number,
                    'earning_type': earning.name,
                    'hours': earning.hours if earning.hours is not None else '',
                    'amount': earning.amount,
                    'ytd': earning.ytd
                })

def create_tax_deductions_csv(paystub_data_list, output_file="extracted_tax_deductions.csv"):
    """Create a CSV file with all tax deductions data."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['employee_name', 'employee_number', 'pay_period_end', 'stub_number', 
                     'deduction_type', 'amount', 'ytd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for paystub in paystub_data_list:
            for deduction in paystub.tax_deductions:
                writer.writerow({
                    'employee_name': paystub.employee_name,
                    'employee_number': paystub.employee_number,
                    'pay_period_end': paystub.pay_period_end,
                    'stub_number': paystub.stub_number,
                    'deduction_type': deduction.name,
                    'amount': deduction.amount,
                    'ytd': deduction.ytd
                })

def create_summary_csv(paystub_data_list, output_file="extracted_summary.csv"):
    """Create a CSV file with summary data for each paystub."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['employee_name', 'employee_number', 'pay_period_end', 'stub_number', 
                     'pay_rate', 'gross_earnings', 'total_deductions', 'net_earnings']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for paystub in paystub_data_list:
            writer.writerow({
                'employee_name': paystub.employee_name,
                'employee_number': paystub.employee_number,
                'pay_period_end': paystub.pay_period_end,
                'stub_number': paystub.stub_number,
                'pay_rate': paystub.pay_rate,
                'gross_earnings': paystub.gross_earnings,
                'total_deductions': paystub.total_deductions,
                'net_earnings': paystub.net_earnings
            })

def analyze_data(paystub_data_list):
    """Perform some basic analysis on the extracted data."""
    print(f"\n{'='*60}")
    print("DATA ANALYSIS SUMMARY")
    print('='*60)
    
    total_employees = len(set(p.employee_name for p in paystub_data_list if p.employee_name))
    total_paystubs = len(paystub_data_list)
    total_gross = sum(p.gross_earnings for p in paystub_data_list)
    total_net = sum(p.net_earnings for p in paystub_data_list)
    total_deductions = sum(p.total_deductions for p in paystub_data_list)
    
    print(f"Total Employees Processed: {total_employees}")
    print(f"Total Paystubs Processed: {total_paystubs}")
    print(f"Total Gross Earnings: ${total_gross:,.2f}")
    print(f"Total Deductions: ${total_deductions:,.2f}")
    print(f"Total Net Earnings: ${total_net:,.2f}")
    
    # Analyze earnings types
    earnings_types = {}
    for paystub in paystub_data_list:
        for earning in paystub.earnings:
            if earning.name not in earnings_types:
                earnings_types[earning.name] = {'count': 0, 'total_amount': 0, 'total_ytd': 0}
            earnings_types[earning.name]['count'] += 1
            earnings_types[earning.name]['total_amount'] += earning.amount
            earnings_types[earning.name]['total_ytd'] += earning.ytd
    
    print(f"\nEARNINGS BREAKDOWN:")
    for earning_type, data in sorted(earnings_types.items()):
        print(f"  {earning_type:<25}: {data['count']:3d} entries, "
              f"${data['total_amount']:8.2f} current, ${data['total_ytd']:12.2f} YTD")
    
    # Analyze tax deductions
    tax_types = {}
    for paystub in paystub_data_list:
        for tax in paystub.tax_deductions:
            if tax.name not in tax_types:
                tax_types[tax.name] = {'count': 0, 'total_amount': 0, 'total_ytd': 0}
            tax_types[tax.name]['count'] += 1
            tax_types[tax.name]['total_amount'] += tax.amount
            tax_types[tax.name]['total_ytd'] += tax.ytd
    
    print(f"\nTAX DEDUCTIONS BREAKDOWN:")
    for tax_type, data in sorted(tax_types.items()):
        print(f"  {tax_type:<25}: {data['count']:3d} entries, "
              f"${data['total_amount']:8.2f} current, ${data['total_ytd']:12.2f} YTD")

def main():
    """Extract data from all paystubs and create CSV files."""
    extractor = PaystubExtractor()
    
    # Input directory setup
    TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test-files")
    INPUT_DIR = TEST_FILES_DIR
    
    if not os.path.exists(INPUT_DIR):
        print(f"Input directory does not exist: {INPUT_DIR}")
        return
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in: {INPUT_DIR}")
        return
    
    all_paystub_data = []
    
    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        print(f"Processing: {filename}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Process all pages (or limit for testing)
                for i, page in enumerate(pdf.pages[:10], start=1):  # Limit to first 10 for demo
                    paystub_data = extractor.extract_paystub_data(page)
                    
                    # Only add if we got meaningful data
                    if paystub_data.employee_name or paystub_data.employee_number:
                        all_paystub_data.append(paystub_data)
                        print(f"  Extracted data for page {i}: {paystub_data.employee_name}")
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print(f"\nTotal paystubs extracted: {len(all_paystub_data)}")
    
    if all_paystub_data:
        # Create CSV files
        create_earnings_csv(all_paystub_data, "clean_earnings.csv")
        create_tax_deductions_csv(all_paystub_data, "clean_tax_deductions.csv")
        create_summary_csv(all_paystub_data, "clean_summary.csv")
        
        print(f"\nGenerated CSV files:")
        print(f"  - clean_earnings.csv")
        print(f"  - clean_tax_deductions.csv")
        print(f"  - clean_summary.csv")
        
        # Perform analysis
        analyze_data(all_paystub_data)
    
    print(f"\n{'='*60}")
    print("EXTRACTION COMPLETE!")
    print('='*60)

if __name__ == "__main__":
    main()