#!/usr/bin/env python3
"""
IMAP Debug Test - Detailed IMAP Protocol Debugging and Diagnostics

AUTHENTICATION METHOD:
- Basic Authentication with IMAP protocol
- Uses app passwords for secure authentication
- Detailed protocol-level debugging enabled

WHAT IT DOES:
- Provides comprehensive IMAP protocol debugging
- Tests connection to Outlook IMAP servers with detailed logging
- Validates folder access and message counting
- Shows raw IMAP protocol communication
- Helps troubleshoot IMAP connectivity issues

MICROSOFT REQUIREMENTS:
1. IMAP Access Setup:
   - Enable IMAP in Outlook settings (Settings > View all > Mail > Sync email)
   - IMAP server: outlook.office365.com, Port: 993, SSL: Yes

2. App Password Setup (Required):
   - Enable 2FA on Microsoft account
   - Generate app password specifically for "Mail" application
   - Use 16-character app password (not regular password)
   - Store in OUTLOOK_APP_PASSWORD environment variable

3. Account Configuration:
   - Two-factor authentication enabled
   - IMAP access enabled in account settings
   - Basic authentication allowed (being deprecated)

DEBUGGING FEATURES:
- IMAP protocol debugging (imaplib.Debug = 4)
- Step-by-step connection process
- Raw protocol command/response logging
- Folder enumeration and access testing
- Message count verification

ADVANTAGES:
- Deep protocol-level debugging
- Raw IMAP command visibility
- Detailed error analysis
- Troubleshooting connectivity issues

LIMITATIONS:
- Very verbose output (debug mode)
- Requires app passwords
- Basic auth may be deprecated
- IMAP protocol limitations vs modern APIs

SETUP STEPS:
1. Enable IMAP in Outlook account settings
2. Enable 2FA and generate Mail app password
3. Add EMAIL_ADDRESS and OUTLOOK_APP_PASSWORD to .env
4. Run script to see detailed IMAP communication

USE CASES:
- Troubleshooting IMAP connectivity problems
- Understanding IMAP protocol behavior
- Debugging authentication issues
- Learning IMAP command sequences
- Protocol-level analysis

IMAP PROTOCOL TESTING:
- SSL connection establishment
- LOGIN command authentication
- CAPABILITY command support
- LIST command for folder enumeration
- SELECT command for folder access
- Message count retrieval

OUTPUT INCLUDES:
- Raw IMAP commands sent
- Server responses received
- SSL/TLS handshake details
- Authentication success/failure
- Folder structure and permissions
"""

import imaplib
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD

# Enable detailed IMAP debugging
imaplib.Debug = 4

def test_imap_connection():
    """Test IMAP connection with detailed logging"""
    print(f"Testing IMAP connection for: {EMAIL_ADDRESS}")
    print(f"Using app password: {OUTLOOK_APP_PASSWORD[:4]}****{OUTLOOK_APP_PASSWORD[-4:]}")
    
    try:
        print("\n1. Connecting to outlook.office365.com:993...")
        imap = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        print("✅ SSL connection established")
        
        print("\n2. Attempting login...")
        imap.login(EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD)
        print("✅ Login successful!")
        
        print("\n3. Listing folders...")
        status, folders = imap.list()
        if status == 'OK':
            print("✅ Folders accessible:")
            for folder in folders[:10]:  # Show first 10 folders
                print(f"   {folder}")
        
        print("\n4. Selecting INBOX...")
        status, count = imap.select('INBOX')
        if status == 'OK':
            print(f"✅ INBOX selected. Messages: {count[0].decode()}")
        
        print("\n5. Checking for Sent Items...")
        status, folders = imap.list()
        sent_folders = [f for f in folders if b'Sent' in f]
        print(f"✅ Found sent folders: {sent_folders}")
        
        imap.logout()
        print("\n🎉 All tests passed! IMAP is working correctly.")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"\n❌ IMAP Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imap_connection()