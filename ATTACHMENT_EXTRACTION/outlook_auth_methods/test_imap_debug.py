#!/usr/bin/env python3
"""
Test IMAP connection with detailed debugging
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