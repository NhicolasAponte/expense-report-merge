# Email Attachment Downloader using ExchangeLib

This script downloads attachments from sent emails in your Outlook/Exchange account.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install exchangelib
   ```

2. **Configure Credentials**
   Edit `env_vars.py` and replace the placeholder values:
   ```python
   EMAIL_ADDRESS = "your-email@company.com"  # Your actual email
   OUTLOOK_PASSWORD = "your-password"        # Your actual password
   ```

3. **Configure Settings**
   Adjust these settings in `env_vars.py` if needed:
   - `EXCHANGE_SERVER`: Default is "outlook.office365.com" (works for most Office 365 accounts)
   - `EXCHANGE_VERSION`: Default is "Exchange2016" (works for most modern Exchange servers)
   - `OUTPUT_DIR`: Where to save downloaded attachments

## Usage

### Basic Usage
```bash
python download_email_attachments.py
```

This will:
- Connect to your Exchange/Outlook account
- Search sent emails from the last 30 days
- Download all attachments to the configured output directory

### Customization Options

You can modify these variables in the `main()` function:

- **`DAYS_BACK`**: Number of days to look back (default: 30)
- **`SEARCH_SUBJECT`**: Filter emails by subject text (default: None for all emails)

Example modifications:
```python
DAYS_BACK = 7  # Look back only 7 days
SEARCH_SUBJECT = "invoice"  # Only emails with "invoice" in subject
```

## Output Structure

Attachments are organized in folders by email:
```
C:\Users\nflores\Desktop\attachments\
├── 20241003_143022_Meeting Notes/
│   ├── presentation.pdf
│   └── agenda.docx
├── 20241002_091545_Invoice from ABC Corp/
│   └── invoice_12345.pdf
└── 20241001_154433_Project Files/
    ├── project_specs.xlsx
    └── timeline.pdf
```

Each folder is named with:
- Date and time the email was sent (YYYYMMDD_HHMMSS)
- First 50 characters of the email subject

## Features

- **Automatic folder organization**: Each email's attachments go in a separate folder
- **Duplicate handling**: If a file already exists, a number is appended
- **Comprehensive logging**: Shows progress and any errors
- **Safe filename handling**: Removes invalid characters from folder names
- **Multiple attachment types**: Handles file attachments (skips embedded emails)

## Troubleshooting

### Authentication Issues
- Make sure your email and password are correct
- If using 2FA, you may need an app password instead of your regular password
- For corporate accounts, check with IT about Exchange server settings

### Connection Issues
- Verify the `EXCHANGE_SERVER` setting (usually "outlook.office365.com" for Office 365)
- Try different `EXCHANGE_VERSION` values if connection fails
- Check if your organization blocks external Exchange connections

### Common Exchange Versions
- `Exchange2007_SP1`
- `Exchange2010`
- `Exchange2013`
- `Exchange2016` (default, works for most Office 365)
- `Exchange2019`

## Security Notes

- Keep your credentials secure and never commit them to version control
- Consider using environment variables for sensitive information
- The script only reads emails and downloads attachments - it doesn't modify or delete anything