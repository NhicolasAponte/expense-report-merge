import os
from pathlib import Path

# for this script to work, the default pdf viewer needs to be adobe or foxit 
def print_all_files(directory):
    directory = Path(directory)
    for file in directory.iterdir():
        if file.is_file() and file.suffix.lower() == '.pdf':
            print(f"Sending to printer: {file.name}")
            # Use os.startfile with the 'print' operation on Windows
            os.startfile(file, "print")

if __name__ == "__main__":
    # folder = r"C:\Users\nflores\Desktop\temp"
    folder = r"C:\Users\nflores\Desktop\found-pdfs"  # Change this to your target directory
    print_all_files(folder)