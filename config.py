import os

LOCAL_DESKTOP_TEMP = r"C:\Users\nflores\Desktop\temp"
LOCAL_ORIGINALS_DIR = r"C:\Users\nflores\Desktop\temp\originals"

SCANNED_PDFS = r"C:\Users\nflores\Desktop\temp\scanned-files"

AR_SCANNED_BATCHES = r"\\mhk-accounting\ar$\Batch Holds"

PRODUCTION_INPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "invoices-to-process")
PRODUCTION_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "ocr-pdfs")

