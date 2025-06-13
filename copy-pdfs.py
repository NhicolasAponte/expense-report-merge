import os
import shutil
from pathlib import Path

def get_file_names_from_txt(txt_path):
    """
    Reads file names from a text file, one per line, and returns a list.
    Ignores empty lines and strips whitespace.
    """
    txt_path = Path(txt_path)
    with open(txt_path, "r", encoding="utf-8") as f:
        file_names = [line.strip() for line in f if line.strip()]
    return file_names

# Example usage:
# files_to_find = get_file_names_from_txt("list_file.txt")

def copy_files_by_name(file_names, search_dir, out_dir):
    """
    Searches for each file name in search_dir (and subdirs), and copies found files to out_dir.
    """
    search_dir = Path(search_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    for file_name in file_names:
        found = False
        print(f"Searching for: {file_name}")
        for path in search_dir.rglob("*"):
            print(f"Checking: {path}")
            if path.is_file() and file_name.lower() in path.name.lower():
                shutil.copy2(path, out_dir / path.name)
                print(f"Copied: {path} -> {out_dir / path.name}")
                found = True
                count += 1
                break  # Remove this break if you want to copy all matches, not just the first
        if not found:
            print(f"File not found: {file_name}")

    print(f"Total files found and copied: {count}") 

if __name__ == "__main__":
    # Example usage:
    search_directory = r"C:\Users\nflores\Invoices"
    output_directory = r"C:\Users\nflores\Desktop\found-pdfs"
    list_file_path = r"C:\Users\nflores\Desktop\temp\list_file.txt"

    files_to_find = get_file_names_from_txt(list_file_path)
    # print(f"Files to find: {files_to_find}")
    # print(len(files_to_find))
    copy_files_by_name(files_to_find, search_directory, output_directory)