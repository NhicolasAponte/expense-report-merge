#!/usr/bin/env python3
"""
Simple test script to check Exchange connection
"""

from exchangelib import Credentials, Account, DELEGATE
from env_vars import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD

def test_connection():
    """Test basic connection to Exchange"""
    try:
        print(f"Testing connection for: {EMAIL_ADDRESS}")
        print(f"Using app password: {OUTLOOK_APP_PASSWORD[:4]}****{OUTLOOK_APP_PASSWORD[-4:]}")
        
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