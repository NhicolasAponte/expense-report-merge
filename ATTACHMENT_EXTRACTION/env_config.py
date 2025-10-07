#!/usr/bin/env python3
"""
Environment configuration using python-dotenv
This safely loads environment variables from a .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)

# Email credentials
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
OUTLOOK_PASSWORD = os.getenv('OUTLOOK_PASSWORD')
OUTLOOK_APP_PASSWORD = os.getenv('OUTLOOK_APP_PASSWORD')

# Personal Azure app credentials
CLIENT_ID = os.getenv('CLIENT_ID')
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Work email credentials
WORK_EMAIL_ADDRESS = os.getenv('WORK_EMAIL_ADDRESS')
WORK_PASSWORD = os.getenv('WORK_PASSWORD')
WORK_APP_PASSWORD = os.getenv('WORK_APP_PASSWORD')

WORK_CLIENT_ID = os.getenv('WORK_CLIENT_ID')
WORK_TENANT_ID = os.getenv('WORK_TENANT_ID')
WORK_CLIENT_SECRET = os.getenv('WORK_CLIENT_SECRET')

# Gmail credentials
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# Exchange server configuration
EXCHANGE_SERVER = os.getenv('EXCHANGE_SERVER', 'outlook.office365.com')
EXCHANGE_VERSION = os.getenv('EXCHANGE_VERSION', 'Exchange2016')

# Folder configuration
SENT_ITEMS_FOLDER = os.getenv('SENT_ITEMS_FOLDER', 'Sent Items')

# Output directory for downloaded attachments
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/Users/nhic/Desktop/attachments')

def validate_credentials():
    """Validate that required environment variables are set"""
    required_vars = {
        'EMAIL_ADDRESS': EMAIL_ADDRESS,
        'OUTLOOK_APP_PASSWORD': OUTLOOK_APP_PASSWORD,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    return True

def print_config():
    """Print current configuration (without showing passwords)"""
    print("🔧 Current Configuration:")
    print(f"   EMAIL_ADDRESS: {EMAIL_ADDRESS}")
    print(f"   OUTLOOK_APP_PASSWORD: {'*' * 8 if OUTLOOK_APP_PASSWORD else 'Not set'}")
    print(f"   WORK_EMAIL_ADDRESS: {WORK_EMAIL_ADDRESS}")
    print(f"   WORK_PASSWORD: {'*' * 8 if WORK_PASSWORD else 'Not set'}")
    print(f"   GMAIL_ADDRESS: {GMAIL_ADDRESS}")
    print(f"   GMAIL_PASSWORD: {'*' * 8 if GMAIL_PASSWORD else 'Not set'}")
    print(f"   CLIENT_ID: {CLIENT_ID}")
    print(f"   TENANT_ID: {TENANT_ID}")
    print(f"   EXCHANGE_SERVER: {EXCHANGE_SERVER}")
    print(f"   OUTPUT_DIR: {OUTPUT_DIR}")

if __name__ == "__main__":
    print("🌍 Environment Configuration Test")
    print("=" * 40)
    print_config()
    print()
    
    if validate_credentials():
        print("✅ Environment configuration is valid!")
    else:
        print("❌ Environment configuration has issues.")