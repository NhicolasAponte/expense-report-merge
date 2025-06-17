import os
import sys

def find_pdf(search_string, directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf') and search_string.lower() in file.lower():
                return os.path.join(root, file)
    return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf-lookup.py <search_string> <directory>")
        sys.exit(1)
    search_string = sys.argv[1]
    directory = sys.argv[2]
    result = find_pdf(search_string, directory)
    if result:
        print(result)
    else:
        print("No matching PDF found.")