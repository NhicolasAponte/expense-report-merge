#!/usr/bin/env python3
"""
Comprehensive IMAP connection test with multiple authentication methods
"""

import imaplib
import base64
from env_vars import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD

def test_basic_auth():
    """Test basic LOGIN authentication"""
    print("🔐 Testing Basic LOGIN Authentication")
    try:
        imap = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        imap.login(EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD)
        print("✅ Basic LOGIN successful!")
        imap.logout()
        return True
    except Exception as e:
        print(f"❌ Basic LOGIN failed: {e}")
        return False

def test_plain_auth():
    """Test PLAIN SASL authentication"""
    print("\n🔐 Testing PLAIN SASL Authentication")
    try:
        imap = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        
        # Create PLAIN auth string: \0username\0password
        auth_string = f"\0{EMAIL_ADDRESS}\0{OUTLOOK_APP_PASSWORD}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        # Try AUTHENTICATE PLAIN
        imap.authenticate('PLAIN', lambda x: auth_bytes)
        print("✅ PLAIN SASL authentication successful!")
        imap.logout()
        return True
    except Exception as e:
        print(f"❌ PLAIN SASL authentication failed: {e}")
        return False

def test_different_servers():
    """Test different IMAP server addresses"""
    servers = [
        "outlook.office365.com",
        "imap-mail.outlook.com", 
        "imap.outlook.com"
    ]
    
    print("\n🌐 Testing Different IMAP Servers")
    for server in servers:
        try:
            print(f"   Trying {server}...")
            imap = imaplib.IMAP4_SSL(server, 993)
            imap.login(EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD)
            print(f"✅ {server} - Login successful!")
            imap.logout()
            return server
        except Exception as e:
            print(f"❌ {server} - Failed: {e}")
    
    return None

def check_account_settings():
    """Display account configuration tips"""
    print("\n⚙️  Account Configuration Checklist:")
    print("   1. 2FA enabled: ✓ (confirmed)")
    print("   2. App password created: ✓ (confirmed)")
    print("   3. IMAP enabled: ✓ (confirmed)")
    print("   4. Check these additional settings:")
    print("      - Go to outlook.com → Settings (⚙️) → View all Outlook settings")
    print("      - Mail → Sync email → POP and IMAP")
    print("      - Ensure 'Let devices and apps use IMAP' is ON")
    print("      - Check 'Server Settings' section for any restrictions")
    print("   5. Try creating a NEW app password specifically labeled 'IMAP Client'")

def main():
    print("🧪 Comprehensive IMAP Connection Test")
    print("="*50)
    print(f"Email: {EMAIL_ADDRESS}")
    print(f"App Password: {OUTLOOK_APP_PASSWORD[:4]}****{OUTLOOK_APP_PASSWORD[-4:]}")
    print()
    
    # Test different authentication methods
    success = False
    success |= test_basic_auth()
    success |= test_plain_auth()
    
    if not success:
        # Try different servers
        working_server = test_different_servers()
        if working_server:
            print(f"\n✅ Found working server: {working_server}")
        else:
            print("\n❌ All authentication methods failed")
            check_account_settings()
            
            print("\n🔍 Additional Debugging Steps:")
            print("1. Try creating a NEW app password")
            print("2. Wait 5-10 minutes for settings to propagate")
            print("3. Check Outlook.com security events for blocked sign-ins")
            print("4. Consider using Microsoft Graph API instead of IMAP")

if __name__ == "__main__":
    main()