#!/usr/bin/env python3
"""
ExchangeLib Detailed Test - Advanced Exchange Web Services with Account Switching

AUTHENTICATION METHOD:
- Exchange Web Services (EWS) with comprehensive testing
- Supports both work and personal account authentication
- Tests autodiscovery and manual configuration methods
- App password and regular password support

WHAT IT DOES:
- Provides detailed ExchangeLib connection testing with debug logging
- Tests both autodiscovery and manual Exchange server configuration
- Supports switching between work and personal Microsoft accounts
- Validates folder access and Exchange connectivity
- Comprehensive error reporting and troubleshooting

MICROSOFT REQUIREMENTS:
1. Personal Account Setup:
   - Enable 2FA on Microsoft account
   - Generate app password for "Mail" application  
   - Store in OUTLOOK_APP_PASSWORD environment variable

2. Work Account Setup:
   - Regular domain password or app password
   - Exchange Online or on-premises Exchange access
   - Store credentials in WORK_EMAIL_ADDRESS and WORK_PASSWORD/WORK_APP_PASSWORD

3. Exchange Web Services:
   - EWS enabled on the server
   - Basic authentication allowed
   - Network connectivity to Exchange endpoints

ACCOUNT SWITCHING:
- Set USE_WORK_ACCOUNT = True for work accounts
- Set USE_WORK_ACCOUNT = False for personal accounts
- Automatically chooses appropriate credentials

AUTHENTICATION METHODS TESTED:
1. Autodiscovery:
   - Let ExchangeLib discover server settings
   - Automatic endpoint and version detection
   
2. Manual Configuration:
   - Hardcoded server: outlook.office365.com
   - Exchange 2016 version specification
   - Fallback when autodiscovery fails

ADVANTAGES:
- Comprehensive Exchange protocol testing
- Detailed debug logging for troubleshooting
- Support for multiple account types
- Fallback configuration options

SETUP STEPS:
1. Configure environment variables for desired account type
2. Set USE_WORK_ACCOUNT flag appropriately
3. Install exchangelib: pip install exchangelib
4. Run script with debug output enabled

USE CASES:
- Troubleshooting Exchange connectivity issues
- Testing different account configurations
- Development and debugging Exchange applications
- Validating server settings and authentication

DEBUGGING FEATURES:
- Full ExchangeLib debug logging
- Step-by-step connection process
- Detailed error reporting
- Server response analysis

DEPENDENCIES:
- exchangelib: Python Exchange Web Services client
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from exchangelib import Credentials, Account, DELEGATE, Configuration, Version
from exchangelib.version import EXCHANGE_2016
from env_config import (
    WORK_EMAIL_ADDRESS, WORK_PASSWORD, WORK_APP_PASSWORD,
    EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD
)

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
exchangelib_logger = logging.getLogger('exchangelib')
exchangelib_logger.setLevel(logging.DEBUG)

# Configuration: Choose which account to test
# Set USE_WORK_ACCOUNT = True to test work account, False for personal account
USE_WORK_ACCOUNT = True

if USE_WORK_ACCOUNT:
    email_address = WORK_EMAIL_ADDRESS
    password = WORK_PASSWORD or WORK_APP_PASSWORD  # Try regular password first, then app password
    account_type = "Work"
else:
    email_address = EMAIL_ADDRESS
    password = OUTLOOK_APP_PASSWORD
    account_type = "Personal"

print(f"🔧 Testing {account_type} Account Configuration")
print(f"Email: {email_address}")
print(f"Password: {'***' if password else 'NOT SET'}")
print("=" * 50)
def test_autodiscovery():
    """Test autodiscovery method"""
    print("🔍 Testing Autodiscovery Method")
    print("=" * 40)
    
    try:
        credentials = Credentials(username=email_address, password=password)
        
        print("Step 1: Creating account with autodiscovery...")
        account = Account(
            primary_smtp_address=email_address,
            credentials=credentials,
            autodiscover=True,
            access_type=DELEGATE
        )
        
        print("✅ Autodiscovery successful!")
        return account
        
    except Exception as e:
        print(f"❌ Autodiscovery failed: {e}")
        return None

def test_manual_config():
    """Test manual configuration method"""
    print("\n🔧 Testing Manual Configuration Method")
    print("=" * 40)
    
    try:
        credentials = Credentials(username=email_address, password=password)
        
        # Try manual configuration
        config = Configuration(
            server='outlook.office365.com',
            credentials=credentials,
            version=Version(EXCHANGE_2016)
        )
        
        print("Step 1: Creating account with manual config...")
        account = Account(
            primary_smtp_address=email_address,
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )
        
        print("✅ Manual configuration successful!")
        return account
        
    except Exception as e:
        print(f"❌ Manual configuration failed: {e}")
        return None

def test_account_access(account):
    """Test basic account access"""
    if not account:
        return False
    
    print("\n📧 Testing Account Access")
    print("=" * 40)
    
    try:
        print("Testing inbox access...")
        inbox_count = account.inbox.total_count
        print(f"✅ Inbox accessible. Total emails: {inbox_count}")
        
        print("Testing sent items access...")
        sent_count = account.sent.total_count  
        print(f"✅ Sent items accessible. Total emails: {sent_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Account access failed: {e}")
        return False

def main():
    print("🧪 Detailed ExchangeLib Testing")
    print("=" * 50)
    print(f"Email: {email_address}")
    if password:
        print(f"App Password: {password[:4]}****{password[-4:]}")
    else:
        print("App Password: NOT SET")
    print()
    
    # Try autodiscovery first
    account = test_autodiscovery()
    
    # If autodiscovery fails, try manual config
    if not account:
        account = test_manual_config()
    
    # Test account access if we got a connection
    if account:
        success = test_account_access(account)
        if success:
            print("\n🎉 All tests passed! ExchangeLib is working.")
        else:
            print("\n⚠️  Connection established but account access failed.")
    else:
        print("\n❌ Could not establish connection with either method.")
        print("\n🔍 Troubleshooting suggestions:")
        print("1. Verify the app password is correct and specifically for 'Mail' access")
        print("2. Check if 'Less secure app access' is enabled (if applicable)")
        print("3. Try waiting 10-15 minutes for new app password to propagate")
        print("4. Check Microsoft account security events for blocked attempts")

if __name__ == "__main__":
    main()