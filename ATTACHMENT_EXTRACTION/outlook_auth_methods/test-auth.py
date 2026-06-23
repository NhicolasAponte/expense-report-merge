import os
from exchangelib import Credentials, Account, Configuration, DELEGATE
from exchangelib.protocol import BaseProtocol

# Disable SSL verification warnings (optional, for testing only)
import warnings
warnings.filterwarnings('ignore')

def test_connection():
    print("=== Testing ExchangeLib Connection ===")
    
    # === CONFIGURATION - UPDATE THESE VALUES ===
    EMAIL_ADDRESS = "nhic.aponte@outlook.com"
    APP_PASSWORD = "cpeuddzxycnnwuss"  # Make sure this is correct!
    # ===========================================
    
    try:
        print(f"1. Creating credentials for: {EMAIL_ADDRESS}")
        credentials = Credentials(EMAIL_ADDRESS, APP_PASSWORD)
        
        print("2. Setting up configuration...")
        # For personal Outlook accounts
        config = Configuration(
            server='outlook.office365.com',
            credentials=credentials
        )
        
        print("3. Connecting to account...")
        account = Account(
            primary_smtp_address=EMAIL_ADDRESS,
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )
        
        print("✅ Connection successful!")
        
        # Test basic account info (using correct attributes)
        print("\n4. Account Information:")
        print(f"   - Email: {account.primary_smtp_address}")
        print(f"   - Mailbox type: {account.root}")
        
        # Test folder access
        print("\n5. Testing folder access:")
        try:
            inbox_count = account.inbox.all().count()
            sent_count = account.sent.all().count()
            print(f"   - Inbox count: {inbox_count} items")
            print(f"   - Sent items count: {sent_count} items")
        except Exception as e:
            print(f"   - Folder access error (but connection works): {e}")
        
        # Test reading a few emails from Sent folder
        print("\n6. Testing email retrieval (last 5 sent emails):")
        try:
            sent_items = account.sent.all().order_by('-datetime_received')[:5]
            for i, item in enumerate(sent_items):
                print(f"   {i+1}. {item.subject} ({item.datetime_received})")
        except Exception as e:
            print(f"   - Email retrieval error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed with error: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        
        # More specific error handling
        if "Invalid credentials" in str(e):
            print("\n🔐 Authentication Issue:")
            print("   - Double-check your app password")
            print("   - Ensure 2FA is enabled")
            print("   - Make sure you're using an App Password, not your regular password")
        elif "autodiscover" in str(e).lower():
            print("\n🌐 Connection Issue:")
            print("   - Try the explicit server configuration below")
        
        return False

def test_simple_connection():
    """Even simpler test - just try to connect"""
    print("\n" + "="*50)
    print("=== Simple Connection Test ===")
    
    EMAIL_ADDRESS = "nhic.aponte@outlook.com"
    APP_PASSWORD = "cpeuddzxycnnwuss"
    
    try:
        print("Attempting simple connection...")
        credentials = Credentials(EMAIL_ADDRESS, APP_PASSWORD)
        account = Account(
            EMAIL_ADDRESS,
            credentials=credentials,
            autodiscover=False,
            config=Configuration(
                server='outlook.office365.com',
                credentials=credentials
            )
        )
        
        # Just try to access a basic property
        _ = account.primary_smtp_address
        print("✅ Simple connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Simple connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Outlook Connection Test Script - FIXED VERSION")
    print("=" * 50)
    
    # Double-check the app password
    print("⚠️  REMINDER: Make sure you're using an APP PASSWORD, not your regular password!")
    print("   You can create one at: https://account.live.com/proofs/AppPassword\n")
    
    success = test_connection()
    
    if not success:
        test_simple_connection()
    
    if success:
        print("\n🎉 SUCCESS! You're ready to build the full recovery script.")
        print("\nNext steps:")
        print("1. Keep this authentication working")
        print("2. We'll now build the invoice downloader")
    else:
        print("\n🔴 Authentication still failing.")
        print("\nDouble-check:")
        print("1. Go to https://account.live.com/proofs/AppPassword")
        print("2. Generate a new app password")
        print("3. Copy it EXACTLY as shown")
        print("4. Update the APP_PASSWORD in the script")