# Setup Instructions

## System Dependencies (macOS)

First install required system dependencies using Homebrew:

```bash
# Install Homebrew if not already installed
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install OCR and PDF processing dependencies
brew install tesseract ghostscript qpdf poppler

# Optional: Install additional language packs for Tesseract
# brew install tesseract-lang
```

## Python Environment Setup

### For macOS/Linux:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### For Windows:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
source venv/Scripts/activate

# Install Python dependencies
pip install -r requirements.txt
```
