import os
import csv
from datetime import datetime

def create_test_csv():
    # Get the path to the user's Desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # Base filename
    base_filename = "test-csv.csv"
    output_path = os.path.join(desktop_path, base_filename)
    
    # Check if file exists and create unique filename if needed
    if os.path.exists(output_path):
        # Get current date in MMDD format
        date_suffix = datetime.now().strftime("%m%d")
        filename_with_date = f"test-csv_{date_suffix}.csv"
        output_path = os.path.join(desktop_path, filename_with_date)
    
    # Create the CSV file
    with open(output_path, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["hello python"])
    
    print(f"CSV file created: {output_path}")

if __name__ == "__main__":
    create_test_csv()