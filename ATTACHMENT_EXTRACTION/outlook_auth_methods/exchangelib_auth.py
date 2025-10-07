#!/usr/bin/env python3
"""
Work Email Attachment Extractor - Optimized for Multiple Organizational Accounts

AUTHENTICATION METHOD:
- Exchange Web Services (EWS) with App Passwords
- Simple environment variable configuration
- Supports multiple work accounts

DESIGNED FOR:
- One-time data extraction from multiple work inboxes
- Date range filtering
- Keyword search (Invoice, Paystub, etc.)
- Bulk attachment downloading
- Organizational Exchange accounts

MICROSOFT REQUIREMENTS:
1. App Password Setup for each account:
   - Sign in to work account → Security → App passwords
   - Generate app password for "Mail" application
   - Add to environment variables

2. Environment Variables (.env file):
   WORK_EMAIL_ADDRESS=account1@company.com
   WORK_APP_PASSWORD=your-16-char-app-password
   
   # Additional accounts (optional)
   WORK_EMAIL_ADDRESS_2=account2@company.com
   WORK_APP_PASSWORD_2=second-app-password

CONFIGURATION:
- Change ACCOUNT_TO_USE to switch between configured accounts
- Modify DATE_RANGE_DAYS to set how far back to search
- Update SEARCH_KEYWORDS for specific email filtering
- Set OUTPUT_BASE_DIR for attachment storage location
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

try:
    from exchangelib import (
        Credentials, Account, DELEGATE,
        Message, FileAttachment, ItemAttachment,
        EWSDateTime, EWSTimeZone
    )
    EXCHANGELIB_AVAILABLE = True
except ImportError:
    print("❌ exchangelib not installed. Run: pip install exchangelib")
    EXCHANGELIB_AVAILABLE = False

from env_config import (
    WORK_EMAIL_ADDRESS, WORK_APP_PASSWORD,
    WORK_EMAIL_ADDRESS_2, WORK_APP_PASSWORD_2,
    WORK_EMAIL_ADDRESS_3, WORK_APP_PASSWORD_3,
)

# ================================
# CONFIGURATION - MODIFY AS NEEDED
# ================================

# Which account to use (1, 2, 3, etc.)
ACCOUNT_TO_USE = 1

# Date range (days back from today)
DATE_RANGE_DAYS = 30

# Keywords to search for (case-insensitive, OR logic)
SEARCH_KEYWORDS = ["Invoice", "Paystub", "Receipt", "Statement"]

# Output directory for attachments
OUTPUT_BASE_DIR = r"C:\Users\nflores\Desktop\work_attachments"

# Account configurations
ACCOUNT_CONFIGS = {
    1: {
        'email': WORK_EMAIL_ADDRESS,
        'password': WORK_APP_PASSWORD,
        'name': 'Primary Work Account'
    },
    2: {
        'email': WORK_EMAIL_ADDRESS_2, 
        'password': WORK_APP_PASSWORD_2,
        'name': 'Secondary Work Account'
    },
    3: {
        'email': WORK_EMAIL_ADDRESS_3, 
        'password': WORK_APP_PASSWORD_3,
        'name': 'Third Work Account'
    },
    # Add more accounts here as needed...
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkEmailExtractor:
    """Extract attachments from work email accounts using Exchange Web Services"""
    
    def __init__(self, email_address: str, app_password: str, account_name: str):
        self.email_address = email_address
        self.app_password = app_password
        self.account_name = account_name
        self.account = None
        
    def connect(self) -> bool:
        """Connect to Exchange account"""
        if not EXCHANGELIB_AVAILABLE:
            logger.error("exchangelib package not available")
            return False
            
        try:
            logger.info(f"Connecting to {self.account_name}: {self.email_address}")
            
            credentials = Credentials(
                username=self.email_address,
                password=self.app_password
            )
            
            # Try autodiscovery first
            self.account = Account(
                primary_smtp_address=self.email_address,
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )
            
            # Test connection by accessing inbox count
            try:
                inbox_count = self.account.inbox.total_count
                logger.info(f"✅ Successfully connected to {self.account_name} ({inbox_count} items in inbox)")
            except:
                # If total_count fails, try a simple folder access
                list(self.account.inbox.all()[:1])
                logger.info(f"✅ Successfully connected to {self.account_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.account_name}: {e}")
            return False
    
    def search_emails(self, days_back: int, keywords: List[str]) -> List:
        """Search for emails in date range with keywords"""
        if not self.account:
            logger.error("Not connected to account")
            return []
        
        try:
            # Calculate date range
            timezone = EWSTimeZone.localzone()
            end_date = timezone.localize(datetime.now())
            start_date = end_date - timedelta(days=days_back)
            
            logger.info(f"Searching emails from {start_date.date()} to {end_date.date()}")
            
            # Search in inbox and sent items
            folders_to_search = [self.account.inbox, self.account.sent]
            all_emails = []
            
            for folder in folders_to_search:
                try:
                    folder_name = getattr(folder, 'name', 'Unknown Folder')
                    logger.info(f"Searching folder: {folder_name}")
                    
                    # Base filter: date range
                    emails = folder.filter(
                        datetime_received__gte=start_date,
                        datetime_received__lte=end_date
                    )
                    
                    # Apply keyword filtering
                    matching_emails = []
                    for email in emails:
                        try:
                            subject = str(email.subject) if email.subject else ""
                            
                            # Check if any keyword matches (case-insensitive)
                            if any(keyword.lower() in subject.lower() for keyword in keywords):
                                matching_emails.append(email)
                                logger.info(f"Found matching email: {subject[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error processing email: {e}")
                            continue
                    
                    all_emails.extend(matching_emails)
                    logger.info(f"Found {len(matching_emails)} matching emails in {folder_name}")
                    
                except Exception as e:
                    logger.error(f"Error searching folder: {e}")
                    continue
            
            logger.info(f"Total matching emails found: {len(all_emails)}")
            return all_emails
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    def download_attachments(self, emails: List, output_dir: str) -> int:
        """Download attachments from emails"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        total_downloaded = 0
        
        for i, email in enumerate(emails, 1):
            try:
                subject = str(email.subject) if email.subject else "No_Subject"
                logger.info(f"Processing email {i}/{len(emails)}: {subject[:50]}...")
                
                # Check if email has attachments
                if not hasattr(email, 'attachments') or not email.attachments:
                    logger.info("  No attachments found")
                    continue
                
                # Create folder for this email
                try:
                    email_date = email.datetime_received.strftime("%Y%m%d_%H%M%S")
                except:
                    email_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                email_folder = output_path / f"{email_date}_{safe_subject}"
                email_folder.mkdir(exist_ok=True)
                
                # Download each attachment
                attachment_count = 0
                for attachment in email.attachments:
                    if isinstance(attachment, FileAttachment):
                        try:
                            filename = str(attachment.name) if attachment.name else f"attachment_{total_downloaded}"
                            # Clean filename
                            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                            filepath = email_folder / filename
                            
                            # Get attachment content
                            content = attachment.content
                            if hasattr(content, 'decode'):
                                # If it's base64 encoded, decode it
                                import base64
                                try:
                                    content = base64.b64decode(content)
                                except:
                                    pass
                            
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            
                            total_downloaded += 1
                            attachment_count += 1
                            logger.info(f"  ✅ Downloaded: {filename}")
                            
                        except Exception as e:
                            logger.error(f"  ❌ Failed to download {filename}: {e}")
                    
                    elif isinstance(attachment, ItemAttachment):
                        logger.info(f"  ⏭️  Skipping embedded email: {getattr(attachment, 'name', 'Unknown')}")
                
                if attachment_count > 0:
                    logger.info(f"  📁 Saved {attachment_count} attachments to: {email_folder.name}")
                
            except Exception as e:
                logger.error(f"Error processing email {i}: {e}")
        
        logger.info(f"🎉 Total attachments downloaded: {total_downloaded}")
        logger.info(f"📁 Saved to: {output_path}")
        return total_downloaded


def validate_environment():
    """Validate that required environment variables are set"""
    config = ACCOUNT_CONFIGS.get(ACCOUNT_TO_USE)
    
    if not config:
        logger.error(f"Account {ACCOUNT_TO_USE} not configured in ACCOUNT_CONFIGS")
        return False
    
    if not config['email']:
        logger.error(f"Missing email address for account {ACCOUNT_TO_USE}")
        logger.error("Please set WORK_EMAIL_ADDRESS in your .env file")
        return False
    
    if not config['password']:
        logger.error(f"Missing app password for account {ACCOUNT_TO_USE}")
        logger.error("Please set WORK_APP_PASSWORD in your .env file")
        return False
    
    return True


def main():
    """Main extraction function"""
    print("=" * 60)
    print("Work Email Attachment Extractor")
    print("=" * 60)
    
    # Check if exchangelib is available
    if not EXCHANGELIB_AVAILABLE:
        print("❌ Required package 'exchangelib' is not installed.")
        print("Please install it with: pip install exchangelib")
        return
    
    # Validate configuration
    if not validate_environment():
        return
    
    config = ACCOUNT_CONFIGS[ACCOUNT_TO_USE]
    
    # Display configuration
    print(f"Account: {config['name']}")
    print(f"Email: {config['email']}")
    print(f"Date Range: Last {DATE_RANGE_DAYS} days")
    print(f"Keywords: {', '.join(SEARCH_KEYWORDS)}")
    print(f"Output Directory: {OUTPUT_BASE_DIR}")
    print("-" * 60)
    
    # Create extractor and connect
    extractor = WorkEmailExtractor(
        email_address=config['email'],
        app_password=config['password'],
        account_name=config['name']
    )
    
    if not extractor.connect():
        logger.error("Failed to connect to account")
        logger.error("\nTroubleshooting tips:")
        logger.error("1. Verify your app password is correct and for 'Mail' access")
        logger.error("2. Check that your work account allows EWS connections")
        logger.error("3. Ensure the email address is correct")
        return
    
    # Search for emails
    emails = extractor.search_emails(DATE_RANGE_DAYS, SEARCH_KEYWORDS)
    
    if not emails:
        logger.info("No matching emails found")
        logger.info(f"Try adjusting DATE_RANGE_DAYS ({DATE_RANGE_DAYS}) or SEARCH_KEYWORDS {SEARCH_KEYWORDS}")
        return
    
    # Download attachments
    account_output_dir = os.path.join(OUTPUT_BASE_DIR, f"account_{ACCOUNT_TO_USE}_{config['email'].split('@')[0]}")
    downloaded_count = extractor.download_attachments(emails, account_output_dir)
    
    print("=" * 60)
    print(f"EXTRACTION COMPLETE")
    print(f"Emails processed: {len(emails)}")
    print(f"Attachments downloaded: {downloaded_count}")
    print(f"Location: {account_output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()