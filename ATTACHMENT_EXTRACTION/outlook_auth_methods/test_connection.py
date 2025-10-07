#!/usr/bin/env python3
"""
ExchangeLib Simple Connection Test - Basic Exchange Web Services Authentication

AUTHENTICATION METHOD:
- Exchange Web Services (EWS) with basic authentication
- Uses ExchangeLib Python library for Exchange protocol
- App password authentication for security

WHAT IT DOES:
- Tests connection to Microsoft Exchange using ExchangeLib
- Performs autodiscovery to find Exchange server settings
- Validates access to inbox and sent items folders
- Simple connectivity verification

MICROSOFT REQUIREMENTS:
1. App Password Setup (Required):
   - Enable 2FA on Microsoft account
   - Generate app password for "Mail" application
   - Use 16-character app password (not regular password)
   - Store in OUTLOOK_APP_PASSWORD environment variable

2. Exchange Web Services:
   - EWS must be enabled (default for most accounts)
   - Basic authentication allowed for EWS
   - Compatible with Exchange Online and on-premises

ADVANTAGES:
- Rich Exchange protocol features
- Automatic server discovery
- Full folder and item access
- Better than IMAP for Exchange-specific features

AUTHENTICATION FLOW:
1. Create credentials with email and app password
2. Use ExchangeLib autodiscovery to find server
3. Establish account connection
4. Test folder access (inbox, sent items)

SETUP STEPS:
1. Enable 2FA on Microsoft account
2. Generate app password for Mail
3. Add EMAIL_ADDRESS and OUTLOOK_APP_PASSWORD to .env
4. Install exchangelib: pip install exchangelib
5. Run script to test connection

USE CASES:
- Exchange-specific email operations
- Calendar and contacts access
- Rich email metadata and properties
- Organizational Exchange servers

LIMITATIONS:
- Requires app passwords (basic auth)
- Microsoft may deprecate basic auth for EWS
- More complex than IMAP for simple operations
- Heavier protocol overhead

DEPENDENCIES:
- exchangelib: Python Exchange Web Services client
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchangelib import Credentials, Account, DELEGATE
from env_config import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD

def test_connection():
    """Test basic connection to Exchange"""
    try:
        print(f"Testing connection for: {EMAIL_ADDRESS}")
        if OUTLOOK_APP_PASSWORD:
            print(f"Using app password: {OUTLOOK_APP_PASSWORD[:4]}****{OUTLOOK_APP_PASSWORD[-4:]}")
        else:
            print("No app password configured")
            return False
        
        # Create credentials with app password
        credentials = Credentials(username=EMAIL_ADDRESS, password=OUTLOOK_APP_PASSWORD)
        
        # Try to create account with autodiscovery (let exchangelib figure out settings)
        print("Attempting autodiscovery...")
        account = Account(
            primary_smtp_address=EMAIL_ADDRESS,
            credentials=credentials,
            autodiscover=True,
            access_type=DELEGATE
        )
        
        # Test basic access
        print("Testing basic access...")
        inbox_count = len(list(account.inbox.all()[:1]))  # Just get one item to test
        print(f"✅ Connection successful! Inbox accessible.")
        
        # Test sent items access
        print("Testing sent items access...")
        sent_count = len(list(account.sent.all()[:1]))  # Just get one item to test
        print(f"✅ Sent items accessible!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()