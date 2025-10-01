import os

# macOS-compatible paths using cross-platform path construction
LOCAL_DESKTOP_TEMP = os.path.join(os.path.expanduser("~"), "Desktop", "temp")
LOCAL_ORIGINALS_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "temp", "originals")

SCANNED_PDFS = os.path.join(os.path.expanduser("~"), "Desktop", "temp", "scanned-files")

# Network share - needs to be mounted in macOS first
# Mount via: Finder -> Go -> Connect to Server -> smb://mhk-accounting/ar$
# Or update this path to match your mounted location
AR_SCANNED_BATCHES = "/Volumes/ar$/Batch Holds"  # Update if network share is mounted differently

# These are already cross-platform compatible
PRODUCTION_INPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "invoices-to-process")
PRODUCTION_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "ocr-pdfs")

UMB_INPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "umb-reports")
UMB_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "umb-reports", "merged-pdfs")
UMB_PROCESSED_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "umb-reports", "processed")