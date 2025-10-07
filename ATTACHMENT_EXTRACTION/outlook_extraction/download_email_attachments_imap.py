#!/usr/bin/env python3
"""
Download attachments from sent emails using IMAP (more compatible with Outlook.com).

This script connects to Outlook using IMAP, searches through sent emails,
and downloads any attachments found.
"""

import os
import email
import imaplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import re

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import EMAIL_ADDRESS, OUTLOOK_APP_PASSWORD, OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IMAPAttachmentDownloader:
    """Download attachments from Outlook sent emails using IMAP."""
    
    def __init__(self, email_address: str, password: str):
        """
        Initialize the IMAP connection.
        
        Args:
            email_address: Email address for authentication
            password: App password for authentication
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = "outlook.office365.com"
        self.imap_port = 993
        self.connection = None
        
    def connect(self) -> bool:
        """
        Establish connection to IMAP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
            
            # Create IMAP connection
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            self.connection.login(self.email_address, self.password)
            
            logger.info(f"Successfully connected to IMAP server for {self.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            return False
    
    def get_sent_emails_with_attachments(self, days_back: int = 30, search_subject: str = None) -> list:
        """
        Retrieve sent emails with attachments from the specified time period.
        
        Args:
            days_back: Number of days to look back for emails
            search_subject: Optional subject text to filter emails
            
        Returns:
            List of email message objects with attachments
        """
        if not self.connection:
            logger.error("Not connected to IMAP server")
            return []
        
        try:
            # Select the Sent folder
            self.connection.select('"Sent Items"')
            
            # Calculate date for search (IMAP date format)
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Build search criteria
            search_criteria = f'SINCE {since_date}'
            if search_subject:
                search_criteria += f' SUBJECT "{search_subject}"'
            
            # Search for emails
            status, message_ids = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return []
            
            message_ids = message_ids[0].split()
            logger.info(f"Found {len(message_ids)} sent emails in the last {days_back} days")
            
            emails_with_attachments = []
            
            for msg_id in message_ids:
                try:
                    # Fetch the email
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse the email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Check if email has attachments
                    has_attachments = False
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            has_attachments = True
                            break
                    
                    if has_attachments:
                        emails_with_attachments.append(email_message)
                        
                except Exception as e:
                    logger.error(f"Error processing email ID {msg_id}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(emails_with_attachments)} emails with attachments")
            return emails_with_attachments
            
        except Exception as e:
            logger.error(f"Error retrieving sent emails: {str(e)}")
            return []
    
    def download_attachments(self, emails: list, output_dir: str) -> int:
        """
        Download attachments from the provided emails.
        
        Args:
            emails: List of email message objects to process
            output_dir: Directory to save attachments
            
        Returns:
            Number of attachments downloaded
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        
        for email_message in emails:
            try:
                # Get email info
                subject = email_message.get('Subject', 'No Subject')
                date_str = email_message.get('Date', '')
                
                # Create a safe folder name
                safe_subject = re.sub(r'[^\w\s-]', '', subject).strip()[:50]
                safe_subject = re.sub(r'[-\s]+', '_', safe_subject)
                
                # Try to parse date
                try:
                    email_date = email.utils.parsedate_to_datetime(date_str)
                    date_prefix = email_date.strftime("%Y%m%d_%H%M%S")
                except:
                    date_prefix = "unknown_date"
                
                email_folder = Path(output_dir) / f"{date_prefix}_{safe_subject}"
                email_folder.mkdir(exist_ok=True)
                
                logger.info(f"Processing email: {subject}")
                
                # Process attachments
                for part in email_message.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename:
                            # Decode filename if needed
                            if filename.startswith('=?'):
                                filename = str(email.header.make_header(email.header.decode_header(filename)))
                            
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
                                f.write(part.get_payload(decode=True))
                            
                            logger.info(f"Downloaded: {filepath}")
                            downloaded_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing email '{subject}': {str(e)}")
                continue
        
        return downloaded_count
    
    def close(self):
        """Close the IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
    
    def run(self, days_back: int = 30, search_subject: str = None, output_dir: str = OUTPUT_DIR) -> bool:
        """
        Main execution method to download attachments from sent emails.
        
        Args:
            days_back: Number of days to look back for emails
            search_subject: Optional subject text to filter emails
            output_dir: Directory to save attachments
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting IMAP attachment download process...")
        
        try:
            # Connect to IMAP
            if not self.connect():
                return False
            
            # Get sent emails with attachments
            emails = self.get_sent_emails_with_attachments(days_back=days_back, search_subject=search_subject)
            if not emails:
                logger.info("No emails with attachments found")
                return True
            
            # Download attachments
            downloaded_count = self.download_attachments(emails, output_dir)
            
            logger.info(f"Download complete! Downloaded {downloaded_count} attachments to {output_dir}")
            return True
            
        finally:
            self.close()


def main():
    """Main function to run the attachment downloader."""
    
    # Validate environment variables
    if not EMAIL_ADDRESS or not OUTLOOK_APP_PASSWORD:
        logger.error("Please update EMAIL_ADDRESS and OUTLOOK_APP_PASSWORD in .env file with your actual credentials")
        return
    
    # Create downloader instance
    downloader = IMAPAttachmentDownloader(
        email_address=EMAIL_ADDRESS,
        password=OUTLOOK_APP_PASSWORD
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