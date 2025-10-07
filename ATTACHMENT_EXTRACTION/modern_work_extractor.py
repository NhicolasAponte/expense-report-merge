#!/usr/bin/env python3
"""
Modern Work Email Extractor - Microsoft Graph API with OAuth 2.0

AUTHENTICATION METHOD:
- Microsoft Graph API with OAuth 2.0 Device Code Flow
- Modern authentication for organization-managed accounts
- No BasicAuth (deprecated) - uses Microsoft's recommended approach

DESIGNED FOR:
- Organization-managed Microsoft 365 accounts
- One-time data extraction from multiple work inboxes
- Date range filtering and keyword search
- Bulk attachment downloading
- Compliance with modern Microsoft authentication

MICROSOFT REQUIREMENTS FOR ORGANIZATIONAL ACCOUNTS:
1. Azure App Registration (IT Admin Required):
   - Go to https://portal.azure.com → App registrations → New registration
   - Application type: Public client/native (for device flow)
   - API permissions: Mail.Read, Mail.ReadWrite, offline_access
   - Admin consent: REQUIRED for organizational data
   - Copy Application (client) ID

2. Environment Variables (.env file):
   CLIENT_ID=your-azure-app-client-id
   TENANT_ID=your-organization-tenant-id (or 'common')
   
   # Account emails to process
   WORK_EMAIL_ADDRESS=account1@company.com
   WORK_EMAIL_ADDRESS_2=account2@company.com
   WORK_EMAIL_ADDRESS_3=account3@company.com

CONFIGURATION:
- Modify ACCOUNTS_TO_PROCESS to specify which accounts to extract
- Set DATE_RANGE_DAYS for search period
- Update SEARCH_KEYWORDS for filtering
- Configure OUTPUT_BASE_DIR for attachments

ADVANTAGES OVER BASICAUTH:
- Works with MFA-enabled organizational accounts
- Complies with Microsoft's security requirements
- No app passwords needed
- Rich Graph API features
- Future-proof authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests
import time

try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    print("❌ MSAL not installed. Run: pip install msal")
    MSAL_AVAILABLE = False

from env_config import (
    CLIENT_ID, TENANT_ID,
    WORK_EMAIL_ADDRESS, WORK_EMAIL_ADDRESS_2, WORK_EMAIL_ADDRESS_3
)

# ================================
# CONFIGURATION - MODIFY AS NEEDED
# ================================

# Which accounts to process (list of account numbers or 'all')
ACCOUNTS_TO_PROCESS = [1]  # [1, 2, 3] or 'all' for all configured accounts

# Date range (days back from today)
DATE_RANGE_DAYS = 30

# Keywords to search for (case-insensitive, OR logic)
SEARCH_KEYWORDS = ["Invoice", "Paystub", "Receipt", "Statement"]

# Output directory for attachments
OUTPUT_BASE_DIR = r"C:\Users\nflores\Desktop\work_attachments_modern"

# Microsoft Graph API scopes required
SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/offline_access"
]

# Account configurations
ACCOUNT_CONFIGS = {
    1: {
        'email': WORK_EMAIL_ADDRESS,
        'name': 'Primary Work Account'
    },
    2: {
        'email': WORK_EMAIL_ADDRESS_2,
        'name': 'Secondary Work Account'
    },
    3: {
        'email': WORK_EMAIL_ADDRESS_3,
        'name': 'Third Work Account'
    },
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModernWorkEmailExtractor:
    """Extract attachments using Microsoft Graph API with OAuth 2.0"""
    
    def __init__(self, client_id: str, tenant_id: str):
        self.client_id = client_id
        self.tenant_id = tenant_id or "common"
        self.access_token = None
        self.app = None
        
        # Graph API endpoints
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
    def authenticate(self) -> bool:
        """Authenticate using device code flow"""
        if not MSAL_AVAILABLE:
            logger.error("MSAL package not available")
            return False
            
        try:
            # Create MSAL app
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.app = msal.PublicClientApplication(
                client_id=self.client_id,
                authority=authority
            )
            
            logger.info("🔐 Starting Modern Authentication (OAuth 2.0 Device Flow)")
            
            # Try to get token silently first (from cache)
            accounts = self.app.get_accounts()
            result = None
            
            if accounts:
                logger.info("Found cached accounts, attempting silent authentication...")
                result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            
            if not result:
                logger.info("No cached token found. Starting device flow...")
                
                # Initiate device code flow
                flow = self.app.initiate_device_flow(scopes=SCOPES)
                
                if "user_code" not in flow:
                    logger.error("Failed to create device flow")
                    return False
                
                print("\n" + "="*60)
                print("🔑 AUTHENTICATION REQUIRED")
                print("="*60)
                print(f"1. Visit: {flow['verification_uri']}")
                print(f"2. Enter code: {flow['user_code']}")
                print("3. Sign in with your work account")
                print("4. Return here after authentication")
                print("="*60)
                
                # Wait for user to complete authentication
                result = self.app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("✅ Authentication successful!")
                return True
            else:
                logger.error(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def search_emails(self, email_address: str, days_back: int, keywords: List[str]) -> List[Dict]:
        """Search for emails using Microsoft Graph API"""
        if not self.access_token:
            logger.error("Not authenticated")
            return []
        
        try:
            # Calculate date range for Graph API
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            logger.info(f"Searching emails for {email_address} from {start_date.date()}")
            
            # Search in both inbox and sent items
            folders = ["inbox", "sentitems"]
            all_emails = []
            
            for folder in folders:
                try:
                    logger.info(f"Searching {folder}...")
                    
                    # Build Graph API query with date filter
                    url = f"{self.graph_endpoint}/users/{email_address}/mailFolders/{folder}/messages"
                    
                    params = {
                        "$filter": f"receivedDateTime ge {start_date_str}",
                        "$select": "id,subject,receivedDateTime,hasAttachments,from,toRecipients",
                        "$top": 1000  # Adjust if needed
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        emails_data = response.json()
                        folder_emails = emails_data.get("value", [])
                        
                        # Filter by keywords
                        matching_emails = []
                        for email in folder_emails:
                            subject = email.get("subject", "")
                            
                            # Check if any keyword matches (case-insensitive)
                            if any(keyword.lower() in subject.lower() for keyword in keywords):
                                # Only include emails with attachments
                                if email.get("hasAttachments", False):
                                    email["folder"] = folder
                                    matching_emails.append(email)
                                    logger.info(f"Found: {subject[:50]}...")
                        
                        all_emails.extend(matching_emails)
                        logger.info(f"Found {len(matching_emails)} matching emails in {folder}")
                        
                    else:
                        logger.error(f"Error searching {folder}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.error(f"Error searching {folder}: {e}")
                    continue
            
            logger.info(f"Total matching emails with attachments: {len(all_emails)}")
            return all_emails
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    def download_attachments(self, email_address: str, emails: List[Dict], output_dir: str) -> int:
        """Download attachments using Microsoft Graph API"""
        if not self.access_token:
            logger.error("Not authenticated")
            return 0
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        total_downloaded = 0
        
        for i, email in enumerate(emails, 1):
            try:
                email_id = email["id"]
                subject = email.get("subject", "No_Subject")
                folder = email.get("folder", "unknown")
                
                logger.info(f"Processing email {i}/{len(emails)}: {subject[:50]}...")
                
                # Get attachments for this email
                url = f"{self.graph_endpoint}/users/{email_address}/messages/{email_id}/attachments"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"  ❌ Failed to get attachments: {response.status_code}")
                    continue
                
                attachments_data = response.json()
                attachments = attachments_data.get("value", [])
                
                if not attachments:
                    logger.info("  No attachments found")
                    continue
                
                # Create folder for this email
                try:
                    email_date = datetime.fromisoformat(email["receivedDateTime"].replace("Z", "+00:00"))
                    email_date_str = email_date.strftime("%Y%m%d_%H%M%S")
                except:
                    email_date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                email_folder = output_path / f"{email_date_str}_{safe_subject}"
                email_folder.mkdir(exist_ok=True)
                
                # Download each attachment
                attachment_count = 0
                for attachment in attachments:
                    try:
                        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                            filename = attachment.get("name", f"attachment_{total_downloaded}")
                            content_bytes = attachment.get("contentBytes", "")
                            
                            if content_bytes:
                                # Decode base64 content
                                content = base64.b64decode(content_bytes)
                                
                                # Clean filename
                                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                                filepath = email_folder / filename
                                
                                with open(filepath, 'wb') as f:
                                    f.write(content)
                                
                                total_downloaded += 1
                                attachment_count += 1
                                logger.info(f"  ✅ Downloaded: {filename}")
                            
                        else:
                            logger.info(f"  ⏭️  Skipping non-file attachment: {attachment.get('name', 'Unknown')}")
                            
                    except Exception as e:
                        logger.error(f"  ❌ Failed to download attachment: {e}")
                
                if attachment_count > 0:
                    logger.info(f"  📁 Saved {attachment_count} attachments to: {email_folder.name}")
                
            except Exception as e:
                logger.error(f"Error processing email {i}: {e}")
        
        logger.info(f"🎉 Total attachments downloaded: {total_downloaded}")
        logger.info(f"📁 Saved to: {output_path}")
        return total_downloaded


def validate_environment():
    """Validate that required environment variables are set"""
    if not CLIENT_ID:
        logger.error("Missing CLIENT_ID in .env file")
        logger.error("Please register an Azure app and set CLIENT_ID")
        return False
    
    if not TENANT_ID:
        logger.warning("Missing TENANT_ID in .env file")
        logger.info("Using 'common' tenant (works for most cases)")
    
    # Validate accounts
    if ACCOUNTS_TO_PROCESS != 'all':
        for account_num in ACCOUNTS_TO_PROCESS:
            config = ACCOUNT_CONFIGS.get(account_num)
            if not config or not config['email']:
                logger.error(f"Account {account_num} not configured or missing email")
                return False
    
    return True


def main():
    """Main extraction function"""
    print("=" * 70)
    print("Modern Work Email Attachment Extractor (Graph API + OAuth 2.0)")
    print("=" * 70)
    
    # Check dependencies
    if not MSAL_AVAILABLE:
        print("❌ Required package 'msal' is not installed.")
        print("Please install it with: pip install msal")
        return
    
    # Validate configuration
    if not validate_environment():
        return
    
    # Determine which accounts to process
    if ACCOUNTS_TO_PROCESS == 'all':
        accounts_to_process = [num for num, config in ACCOUNT_CONFIGS.items() if config['email']]
    else:
        accounts_to_process = ACCOUNTS_TO_PROCESS
    
    print(f"Accounts to process: {len(accounts_to_process)}")
    print(f"Date Range: Last {DATE_RANGE_DAYS} days")
    print(f"Keywords: {', '.join(SEARCH_KEYWORDS)}")
    print(f"Output Directory: {OUTPUT_BASE_DIR}")
    print("-" * 70)
    
    # Create extractor and authenticate
    extractor = ModernWorkEmailExtractor(
        client_id=CLIENT_ID,
        tenant_id=TENANT_ID
    )
    
    if not extractor.authenticate():
        logger.error("Failed to authenticate")
        logger.error("\nTroubleshooting tips:")
        logger.error("1. Verify CLIENT_ID is correct")
        logger.error("2. Ensure Azure app has required permissions")
        logger.error("3. Check that admin consent has been granted")
        return
    
    # Process each account
    total_emails = 0
    total_attachments = 0
    
    for account_num in accounts_to_process:
        config = ACCOUNT_CONFIGS[account_num]
        
        if not config['email']:
            logger.warning(f"Skipping account {account_num}: No email configured")
            continue
        
        print(f"\n{'='*50}")
        print(f"Processing {config['name']}: {config['email']}")
        print(f"{'='*50}")
        
        # Search for emails
        emails = extractor.search_emails(
            email_address=config['email'],
            days_back=DATE_RANGE_DAYS,
            keywords=SEARCH_KEYWORDS
        )
        
        if not emails:
            logger.info("No matching emails found for this account")
            continue
        
        # Download attachments
        account_output_dir = os.path.join(
            OUTPUT_BASE_DIR, 
            f"account_{account_num}_{config['email'].split('@')[0]}"
        )
        
        downloaded_count = extractor.download_attachments(
            email_address=config['email'],
            emails=emails,
            output_dir=account_output_dir
        )
        
        total_emails += len(emails)
        total_attachments += downloaded_count
        
        print(f"Account {account_num} Summary:")
        print(f"  Emails processed: {len(emails)}")
        print(f"  Attachments downloaded: {downloaded_count}")
        print(f"  Location: {account_output_dir}")
    
    print("=" * 70)
    print(f"EXTRACTION COMPLETE")
    print(f"Total accounts processed: {len(accounts_to_process)}")
    print(f"Total emails processed: {total_emails}")
    print(f"Total attachments downloaded: {total_attachments}")
    print(f"Base location: {OUTPUT_BASE_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()