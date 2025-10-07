#!/usr/bin/env python3
"""
Download attachments from sent emails using exchangelib.

This script connects to Microsoft Exchange/Outlook using exchangelib,
searches through sent emails, and downloads any attachments found.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from exchangelib import (
    Credentials, Account, DELEGATE,
    Message, FileAttachment, ItemAttachment,
    EWSDateTime, EWSTimeZone
)

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env_config import (
    EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD, EXCHANGE_SERVER, 
    EXCHANGE_VERSION, SENT_ITEMS_FOLDER, OUTPUT_DIR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExchangeAttachmentDownloader:
    """Download attachments from Exchange/Outlook sent emails."""
    
    def __init__(self, email: str, password: str, server: str, version: str = "Exchange2016"):
        """
        Initialize the Exchange connection.
        
        Args:
            email: Email address for authentication
            password: Password for authentication
            server: Exchange server address
            version: Exchange version (default: Exchange2016)
        """
        self.email = email
        self.password = password
        self.server = server
        self.version = version
        self.account = None
        
    def connect(self) -> bool:
        """
        Establish connection to Exchange server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create credentials
            credentials = Credentials(username=self.email, password=self.password)
            
            # Create account with autodiscovery
            self.account = Account(
                primary_smtp_address=self.email,
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )
            
            # Test connection by accessing inbox
            _ = self.account.inbox.total_count
            logger.info(f"Successfully connected to Exchange server for {self.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Exchange server: {str(e)}")
            return False
    
    def get_sent_emails(self, days_back: int = 30, search_subject: Optional[str] = None) -> List[Message]:
        """
        Retrieve sent emails from the specified time period.
        
        Args:
            days_back: Number of days to look back for emails (default: 30)
            search_subject: Optional subject text to filter emails
            
        Returns:
            List of sent email messages
        """
        if not self.account:
            logger.error("Not connected to Exchange server")
            return []
        
        try:
            # Calculate date range
            tz = EWSTimeZone.localzone()
            end_date = EWSDateTime.now(tz=tz)
            start_date = end_date - timedelta(days=days_back)
            
            # Access sent items folder
            sent_items = self.account.sent
            
            # Build filter criteria
            filter_criteria = sent_items.filter(datetime_sent__gte=start_date)
            
            if search_subject:
                filter_criteria = filter_criteria.filter(subject__icontains=search_subject)
            
            # Get emails with attachments only
            emails_with_attachments = []
            for email in filter_criteria.order_by('-datetime_sent'):
                if email.attachments:
                    emails_with_attachments.append(email)
            
            logger.info(f"Found {len(emails_with_attachments)} sent emails with attachments")
            return emails_with_attachments
            
        except Exception as e:
            logger.error(f"Error retrieving sent emails: {str(e)}")
            return []
    
    def download_attachments(self, emails: List[Message], output_dir: str) -> int:
        """
        Download attachments from the provided emails.
        
        Args:
            emails: List of email messages to process
            output_dir: Directory to save attachments
            
        Returns:
            Number of attachments downloaded
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        
        for email in emails:
            try:
                # Create subfolder for each email (using date and subject)
                email_date = email.datetime_sent.strftime("%Y%m%d_%H%M%S")
                safe_subject = "".join(c for c in email.subject if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                email_folder = Path(output_dir) / f"{email_date}_{safe_subject}"
                email_folder.mkdir(exist_ok=True)
                
                logger.info(f"Processing email: {email.subject} (sent: {email.datetime_sent})")
                
                for attachment in email.attachments:
                    if isinstance(attachment, FileAttachment):
                        # Handle file attachments
                        filename = attachment.name
                        filepath = email_folder / filename
                        
                        # Avoid overwriting files
                        counter = 1
                        original_filepath = filepath
                        while filepath.exists():
                            name, ext = os.path.splitext(original_filepath)
                            filepath = Path(f"{name}_{counter}{ext}")
                            counter += 1
                        
                        # Save the attachment
                        with open(filepath, 'wb') as f:
                            f.write(attachment.content)
                        
                        logger.info(f"Downloaded: {filepath}")
                        downloaded_count += 1
                        
                    elif isinstance(attachment, ItemAttachment):
                        # Handle embedded email attachments
                        logger.info(f"Skipping embedded email attachment: {attachment.name}")
                        
            except Exception as e:
                logger.error(f"Error processing email '{email.subject}': {str(e)}")
                continue
        
        return downloaded_count
    
    def run(self, days_back: int = 30, search_subject: Optional[str] = None, output_dir: str = OUTPUT_DIR) -> bool:
        """
        Main execution method to download attachments from sent emails.
        
        Args:
            days_back: Number of days to look back for emails
            search_subject: Optional subject text to filter emails
            output_dir: Directory to save attachments
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting attachment download process...")
        
        # Connect to Exchange
        if not self.connect():
            return False
        
        # Get sent emails
        emails = self.get_sent_emails(days_back=days_back, search_subject=search_subject)
        if not emails:
            logger.info("No emails with attachments found")
            return True
        
        # Download attachments
        downloaded_count = self.download_attachments(emails, output_dir)
        
        logger.info(f"Download complete! Downloaded {downloaded_count} attachments to {output_dir}")
        return True


def main():
    """Main function to run the attachment downloader."""
    
    # Validate environment variables
    if not EMAIL_ADDRESS or not OUTLOOK_APP_PASSWORD:
        logger.error("Please update EMAIL_ADDRESS and OUTLOOK_APP_PASSWORD in .env file with your actual credentials")
        return
    
    # Create downloader instance
    downloader = ExchangeAttachmentDownloader(
        email=EMAIL_ADDRESS,
        password=OUTLOOK_APP_PASSWORD,
        server=EXCHANGE_SERVER,
        version=EXCHANGE_VERSION
    )
    
    # Configuration options
    DAYS_BACK = 30  # Look back 30 days
    SEARCH_SUBJECT = None  # Set to filter by subject, e.g., "invoice" or "receipt"
    
    # Run the download process
    success = downloader.run(
        days_back=DAYS_BACK,
        search_subject=SEARCH_SUBJECT,
        output_dir=OUTPUT_DIR
    )
    
    if success:
        logger.info("Attachment download completed successfully!")
    else:
        logger.error("Attachment download failed!")


if __name__ == "__main__":
    main()
