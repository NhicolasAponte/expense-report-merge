# Work Email Attachment Extractor - Usage Guide

## Quick Start for Your Use Case

The `exchangelib_auth.py` script is now optimized for your specific requirements: **accessing multiple work inboxes, date range filtering, keyword search, and bulk attachment downloading**.

## Why This Method is Perfect for You:

✅ **Multiple Work Accounts**: Support for up to 3 work accounts (easily expandable)  
✅ **Simple Setup**: Just app passwords, no OAuth complexity  
✅ **Date Range Filtering**: Built-in date range support  
✅ **Keyword Search**: Search for "Invoice", "Paystub", etc.  
✅ **One-time Use**: Perfect for data extraction  
✅ **Environment Variables**: Easy account switching  

## Setup Steps

### 1. Generate App Passwords (for each work account)
```
1. Sign in to your work Microsoft account
2. Go to Security → Advanced security options → App passwords
3. Click "Create a new app password"
4. Select "Mail" as the application
5. Copy the 16-character app password
6. Repeat for each work account
```

### 2. Configure Environment Variables
Add these to your `.env` file:
```bash
# Primary work account
WORK_EMAIL_ADDRESS=your-email@company.com
WORK_APP_PASSWORD=your-16-char-app-password

# Additional accounts (optional)
WORK_EMAIL_ADDRESS_2=second-email@company.com
WORK_APP_PASSWORD_2=second-app-password

WORK_EMAIL_ADDRESS_3=third-email@company.com
WORK_APP_PASSWORD_3=third-app-password
```

### 3. Install Required Package
```bash
pip install exchangelib
```

## Usage

### Basic Configuration (modify these variables in the script):

```python
# Which account to use (1, 2, or 3)
ACCOUNT_TO_USE = 1

# How many days back to search
DATE_RANGE_DAYS = 30

# Keywords to search for (OR logic)
SEARCH_KEYWORDS = ["Invoice", "Paystub", "Receipt", "Statement"]

# Where to save attachments
OUTPUT_BASE_DIR = r"C:\Users\nflores\Desktop\work_attachments"
```

### Running the Script

```bash
cd ATTACHMENT_EXTRACTION/outlook_auth_methods
python exchangelib_auth.py
```

### Output Structure
```
work_attachments/
├── account_1_username/
│   ├── 20241007_143022_Invoice_from_Vendor/
│   │   ├── invoice_001.pdf
│   │   └── receipt_summary.xlsx
│   └── 20241006_091530_Paystub_October/
│       └── paystub.pdf
```

## Switching Between Accounts

To process different accounts, just change the `ACCOUNT_TO_USE` variable:

```python
# For primary account
ACCOUNT_TO_USE = 1

# For secondary account  
ACCOUNT_TO_USE = 2

# For third account
ACCOUNT_TO_USE = 3
```

## Customizing Search Criteria

### Date Range Examples:
```python
DATE_RANGE_DAYS = 7    # Last week
DATE_RANGE_DAYS = 30   # Last month  
DATE_RANGE_DAYS = 90   # Last quarter
DATE_RANGE_DAYS = 365  # Last year
```

### Keyword Examples:
```python
# For invoices only
SEARCH_KEYWORDS = ["Invoice", "Bill", "Receipt"]

# For payroll documents
SEARCH_KEYWORDS = ["Paystub", "Payroll", "Salary", "Pay Statement"]

# For financial statements
SEARCH_KEYWORDS = ["Statement", "Balance", "Account Summary"]

# For all important documents
SEARCH_KEYWORDS = ["Invoice", "Paystub", "Receipt", "Statement", "Contract", "Agreement"]
```

## Advantages of This Approach

### ✅ **Simplicity**
- No OAuth flows to manage
- No browser authentication required
- Just environment variables

### ✅ **Work Account Optimized**
- Designed for organizational Exchange servers
- Handles multiple company email accounts
- Rich search and filtering capabilities

### ✅ **Perfect for Data Extraction**
- One-time setup
- Bulk processing
- Organized output structure
- Detailed logging

### ✅ **Easily Scalable**
- Add more accounts by updating .env
- Modify search criteria as needed
- Adjust date ranges without code changes

## Troubleshooting

### Common Issues:

**"Failed to connect to account"**
- Verify app password is correct and for 'Mail' access
- Check that work account allows EWS connections
- Ensure email address is correct

**"No matching emails found"**
- Try adjusting DATE_RANGE_DAYS (increase the range)
- Modify SEARCH_KEYWORDS (try broader terms)
- Check if emails actually exist in the account

**"exchangelib not installed"**
- Run: `pip install exchangelib`

## Example Workflow

1. **Setup once**: Generate app passwords, update .env file
2. **Process Account 1**: Set `ACCOUNT_TO_USE = 1`, run script
3. **Process Account 2**: Set `ACCOUNT_TO_USE = 2`, run script  
4. **Process Account 3**: Set `ACCOUNT_TO_USE = 3`, run script
5. **Review results**: Check output directories for all attachments

This approach gives you maximum simplicity while handling your exact requirements for multiple work inboxes, date filtering, keyword search, and attachment extraction.