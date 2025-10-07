#!/usr/bin/env python3
"""
Environment Variables Usage Guide for ATTACHMENT_EXTRACTION

This file demonstrates the standardized approach for using environment variables
across all scripts in the ATTACHMENT_EXTRACTION folder. All scripts should follow 
this pattern for consistency and interchangeability.

Updated: October 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Standard import pattern - all scripts should use this
from env_config import (
    # Personal Account Credentials
    EMAIL_ADDRESS,                  # Personal email address
    OUTLOOK_PASSWORD,              # Personal regular password (if any)
    OUTLOOK_APP_PASSWORD,          # Personal app password (recommended)
    
    # Work Account Credentials  
    WORK_EMAIL_ADDRESS,            # Work email address
    WORK_PASSWORD,                 # Work regular password
    WORK_APP_PASSWORD,             # Work app password
    
    # Gmail Credentials
    GMAIL_ADDRESS,                 # Gmail address
    GMAIL_PASSWORD,                # Gmail app password
    
    # Azure/OAuth Credentials
    CLIENT_ID,                     # Personal Azure app client ID
    TENANT_ID,                     # Personal tenant ID
    CLIENT_SECRET,                 # Personal client secret
    WORK_CLIENT_ID,                # Work Azure app client ID
    WORK_TENANT_ID,                # Work tenant ID
    WORK_CLIENT_SECRET,            # Work client secret
    
    # Configuration
    EXCHANGE_SERVER,               # Exchange server (default: outlook.office365.com)
    EXCHANGE_VERSION,              # Exchange version (default: Exchange2016)
    SENT_ITEMS_FOLDER,             # Sent items folder name
    OUTPUT_DIR                     # Output directory for attachments
)

def get_account_config(use_work_account=False):
    """
    Get account configuration in a standardized, interchangeable way.
    
    Args:
        use_work_account (bool): If True, return work account config, 
                                else return personal account config
    
    Returns:
        dict: Account configuration with email, password, and account_type
    """
    if use_work_account:
        return {
            'email_address': WORK_EMAIL_ADDRESS,
            'password': WORK_PASSWORD or WORK_APP_PASSWORD,  # Prefer app password
            'account_type': 'Work',
            'description': f"Work Account ({WORK_EMAIL_ADDRESS})"
        }
    else:
        return {
            'email_address': EMAIL_ADDRESS,
            'password': OUTLOOK_APP_PASSWORD,  # Always use app password for personal
            'account_type': 'Personal', 
            'description': f"Personal Account ({EMAIL_ADDRESS})"
        }

def get_gmail_config():
    """
    Get Gmail configuration.
    
    Returns:
        dict: Gmail configuration
    """
    return {
        'email_address': GMAIL_ADDRESS,
        'password': GMAIL_PASSWORD,
        'account_type': 'Gmail',
        'description': f"Gmail Account ({GMAIL_ADDRESS})"
    }

def validate_account_config(config):
    """
    Validate that an account configuration has required fields.
    
    Args:
        config (dict): Account configuration from get_account_config()
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not config['email_address']:
        print(f"❌ Email address not configured for {config['account_type']} account")
        return False
    
    if not config['password']:
        print(f"❌ Password not configured for {config['account_type']} account")
        return False
    
    return True

def print_config_summary():
    """Print a summary of all configured accounts."""
    print("🔧 Account Configuration Summary")
    print("=" * 50)
    
    # Personal Account
    personal_config = get_account_config(use_work_account=False)
    status = "✅ Configured" if validate_account_config(personal_config) else "❌ Missing credentials"
    print(f"Personal Account: {personal_config['email_address'] or 'Not set'} - {status}")
    
    # Work Account
    work_config = get_account_config(use_work_account=True)
    status = "✅ Configured" if validate_account_config(work_config) else "❌ Missing credentials"
    print(f"Work Account: {work_config['email_address'] or 'Not set'} - {status}")
    
    # Gmail Account
    gmail_config = get_gmail_config()
    status = "✅ Configured" if validate_account_config(gmail_config) else "❌ Missing credentials"
    print(f"Gmail Account: {gmail_config['email_address'] or 'Not set'} - {status}")
    
    print(f"\nOutput Directory: {OUTPUT_DIR}")
    print(f"Exchange Server: {EXCHANGE_SERVER}")

# Example usage pattern for scripts:
def example_script_pattern():
    """
    Example showing how scripts should be structured to use interchangeable 
    environment variables.
    """
    
    # 1. Choose which account to use (make this configurable)
    USE_WORK_ACCOUNT = True  # Change this to switch between accounts
    USE_GMAIL = False        # Or use Gmail instead
    
    # 2. Get the appropriate configuration
    if USE_GMAIL:
        config = get_gmail_config()
    else:
        config = get_account_config(use_work_account=USE_WORK_ACCOUNT)
    
    # 3. Validate configuration
    if not validate_account_config(config):
        print("Please check your .env file and ensure required credentials are set.")
        return False
    
    # 4. Use the configuration
    print(f"Using {config['description']}")
    print(f"Password: {'*' * 8 if config['password'] else 'Not set'}")
    
    # 5. Pass to your downloader/tester class
    # Example:
    # downloader = SomeDownloader(
    #     email_address=config['email_address'],
    #     password=config['password']
    # )
    
    return True

if __name__ == "__main__":
    print("📋 Environment Variables Usage Guide")
    print("=" * 60)
    print()
    
    print_config_summary()
    print()
    
    print("📝 Example Script Pattern:")
    print("=" * 30)
    example_script_pattern()
    print()
    
    print("💡 Usage Tips:")
    print("- Copy .env.example to .env and fill in your credentials")
    print("- Use env_config import pattern shown above")
    print("- Use get_account_config() for standardized account switching")
    print("- Always validate configurations before using")
    print("- Prefer app passwords over regular passwords for security")