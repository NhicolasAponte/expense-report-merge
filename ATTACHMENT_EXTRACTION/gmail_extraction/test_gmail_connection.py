#!/usr/bin/env python3
"""
Simple Gmail IMAP connection test
"""

import imaplib
from env_vars import GMAIL_ADDRESS, GMAIL_PASSWORD

def test_gmail_connection():
    """Test Gmail IMAP connection"""
    print(f"Testing Gmail IMAP connection for: {GMAIL_ADDRESS}")
    
    if GMAIL_PASSWORD == "your-gmail-app-password-here":
        print("❌ Please update GMAIL_PASSWORD in env_vars.py with your Gmail app password")
        return False
    
    print(f"Using app password: {GMAIL_PASSWORD[:4]}****{GMAIL_PASSWORD[-4:]}")
    
    try:
        print("\n1. Connecting to imap.gmail.com:993...")
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        print("✅ SSL connection established")
        
        print("\n2. Attempting login...")
        imap.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        print("✅ Login successful!")
        
        print("\n3. Listing folders...")
        status, folders = imap.list()
        if status == 'OK':
            print("✅ Folders accessible:")
            sent_folders = []
            for folder in folders[:15]:  # Show first 15 folders
                folder_str = folder.decode('utf-8') if folder else ""
                print(f"   {folder_str}")
                if 'Sent' in folder_str:
                    sent_folders.append(folder_str)
            
            print(f"\n📤 Found sent folders: {sent_folders}")
        
        print("\n4. Testing sent mail access...")
        # Try to select sent mail folder
        sent_folder_names = ['[Gmail]/Sent Mail', 'Sent Mail', 'INBOX.Sent']
        for folder_name in sent_folder_names:
            try:
                status, count = imap.select(f'"{folder_name}"')
                if status == 'OK':
                    print(f"✅ Successfully selected: {folder_name}")
                    print(f"   Messages in folder: {count[0].decode()}")
                    break
            except Exception as e:
                print(f"   Could not select {folder_name}: {e}")
        
        imap.logout()
        print("\n🎉 All tests passed! Gmail IMAP is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Gmail connection failed: {e}")
        return False

if __name__ == "__main__":
    test_gmail_connection()