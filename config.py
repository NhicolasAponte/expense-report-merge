import os

LOCAL_ORIGINALS_DIR = r"C:\Users\nflores\Desktop\Billing\originals"
LOCAL_DESKTOP_TEMP = r"C:\Users\nflores\Desktop\Billing\flat_scans"
LOCAL_OCR_RESULTS = r"C:\Users\nflores\Desktop\Billing\ocr_results"
READY_FOR_INVOICING = r"C:\Users\nflores\Desktop\Billing\invoice_batches"
CSV_OUTPUT = r"C:\Users\nflores\Desktop\Billing\invoice_csvs"

SCANNED_PDFS = r"C:\Users\nflores\Desktop\temp\scanned-files"

AR_SCANNED_BATCHES = r"\\mhk-accounting\ar$\Batch Holds"

PRODUCTION_INPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "invoices-to-process")
PRODUCTION_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "ocr-pdfs")

UMB_INPUT_DIR = r"C:\Users\nflores\Desktop\UMB\input"
UMB_OUTPUT_DIR = r"C:\Users\nflores\Desktop\UMB\output"
UMB_PROCESSED_DIR = r"C:\Users\nflores\Desktop\UMB\input\processed"
