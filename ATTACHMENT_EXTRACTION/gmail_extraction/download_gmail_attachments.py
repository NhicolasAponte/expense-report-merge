#!/usr/bin/env python3
"""
Gmail attachment downloader using IMAP.
This should work with Gmail's app passwords.
"""

import os
import email
import imaplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
import re

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import GMAIL_ADDRESS, GMAIL_PASSWORD, OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GmailAttachmentDownloader:
    """Download attachments from Gmail sent emails using IMAP."""
    
    def __init__(self, email_address: str, password: str):
        """
        Initialize the Gmail IMAP connection.
        
        Args:
            email_address: Gmail address
            password: Gmail app password (not regular password)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.connection = None
        
    def connect(self) -> bool:
        """
        Establish connection to Gmail IMAP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
            
            # Create IMAP connection
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            self.connection.login(self.email_address, self.password)
            
            logger.info(f"Successfully connected to Gmail for {self.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {str(e)}")
            return False
    
    def list_folders(self):
        """List all available folders for debugging"""
        if not self.connection:
            return []
        
        try:
            status, folders = self.connection.list()
            if status == 'OK':
                folder_names = []
                for folder in folders:
                    # Parse folder name from the response
                    folder_str = folder.decode('utf-8')
                    # Extract folder name (usually the last quoted part)
                    parts = folder_str.split('"')
                    if len(parts) >= 3:
                        folder_names.append(parts[-2])
                return folder_names
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            return []
    
    def get_sent_emails_with_attachments(self, days_back: int = 30, search_subject: str = None) -> list:
        """
        Retrieve sent emails with attachments from Gmail.
        
        Args:
            days_back: Number of days to look back for emails
            search_subject: Optional subject text to filter emails
            
        Returns:
            List of email message objects with attachments
        """
        if not self.connection:
            logger.error("Not connected to Gmail")
            return []
        
        try:
            # Gmail uses [Gmail]/Sent Mail for sent emails
            # Try different folder names
            sent_folders = ['[Gmail]/Sent Mail', 'Sent Mail', 'INBOX.Sent', 'Sent']
            selected_folder = None
            
            for folder in sent_folders:
                try:
                    status, count = self.connection.select(f'"{folder}"')
                    if status == 'OK':
                        selected_folder = folder
                        logger.info(f"Selected folder: {folder}")
                        break
                except:
                    continue
            
            if not selected_folder:
                logger.error("Could not find sent mail folder")
                # List available folders for debugging
                folders = self.list_folders()
                logger.info(f"Available folders: {folders}")
                return []
            
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
                                try:
                                    filename = str(email.header.make_header(email.header.decode_header(filename)))
                                except:
                                    pass  # Keep original filename if decode fails
                            
                            filepath = email_folder / filename
                            
                            # Avoid overwriting files
                            counter = 1
                            original_filepath = filepath
                            while filepath.exists():
                                name, ext = os.path.splitext(original_filepath)
                                filepath = Path(f"{name}_{counter}{ext}")
                                counter += 1
                            
                            # Save the attachment
                            try:
                                with open(filepath, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                logger.info(f"Downloaded: {filepath}")
                                downloaded_count += 1
                            except Exception as e:
                                logger.error(f"Error saving attachment {filename}: {e}")
                        
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
        logger.info("Starting Gmail attachment download process...")
        
        try:
            # Connect to Gmail
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
    """Main function to run the Gmail attachment downloader."""
    
    # Validate environment variables
    if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        logger.error("Please update GMAIL_ADDRESS and GMAIL_PASSWORD in .env file")
        return
    
    if GMAIL_PASSWORD == "ShoppingPasswurd69!":
        logger.error("Please update GMAIL_PASSWORD with your actual Gmail app password")
        return
    
    # Create downloader instance
    downloader = GmailAttachmentDownloader(
        email_address=GMAIL_ADDRESS,
        password=GMAIL_PASSWORD
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
        logger.info("Gmail attachment download completed successfully!")
    else:
        logger.error("Gmail attachment download failed!")


if __name__ == "__main__":
    main()