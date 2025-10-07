#!/usr/bin/env python3
"""
Comprehensive IMAP Test - Multiple Basic Authentication Methods

AUTHENTICATION METHOD:
- Basic Authentication (Legacy) with multiple SASL mechanisms
- Tests LOGIN, PLAIN, and different server endpoints
- Uses app passwords for security

WHAT IT DOES:
- Tests multiple IMAP authentication methods against Outlook servers
- Validates different SASL authentication mechanisms
- Tries various server endpoints and configurations
- Provides comprehensive connectivity diagnostics

MICROSOFT REQUIREMENTS:
1. App Password Setup (Required):
   - Sign in to Microsoft account security page
   - Go to Security > Advanced security options
   - Generate new app password for "Mail" application
   - Use this 16-character password (not your regular password)
   - Store in OUTLOOK_APP_PASSWORD environment variable

2. Account Configuration:
   - IMAP must be enabled in Outlook settings
   - Two-factor authentication should be enabled
   - Basic authentication must be allowed (being deprecated)

AUTHENTICATION METHODS TESTED:
1. Basic LOGIN:
   - Standard IMAP LOGIN command
   - Username and app password authentication
   
2. PLAIN SASL:
   - AUTHENTICATE PLAIN mechanism
   - Base64-encoded credentials
   - Alternative to LOGIN command

3. Server Endpoint Testing:
   - outlook.office365.com (primary)
   - imap-mail.outlook.com (alternative)
   - Different port configurations

ADVANTAGES:
- Simple username/password authentication
- No browser interaction required
- Works with existing IMAP libraries
- Direct protocol access

LIMITATIONS:
- Microsoft is deprecating basic auth
- Requires app passwords (security concern)
- No MFA support in authentication flow
- May be disabled in organizational tenants

SETUP STEPS:
1. Enable 2FA on Microsoft account
2. Generate app password for Mail
3. Add EMAIL_ADDRESS and OUTLOOK_APP_PASSWORD to .env
4. Enable IMAP in Outlook settings
5. Run script to test connectivity

USE CASES:
- Legacy application integration
- Simple IMAP protocol testing
- Troubleshooting connectivity issues
- Backup authentication when OAuth fails

TROUBLESHOOTING:
- If LOGIN fails, basic auth may be disabled
- Try different server endpoints
- Verify app password is for "Mail" specifically
- Check if organizational policies block basic auth
"""

import imaplib
import base64
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD

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