#!/usr/bin/env python3
"""
Microsoft Graph API approach for downloading email attachments
This is a more reliable method for Outlook.com accounts
"""

import requests
import json
import os
from pathlib import Path
import base64
from datetime import datetime, timedelta
import re

# NOTE: This requires additional setup:
# 1. Register an Azure app at https://portal.azure.com
# 2. Get client_id and client_secret
# 3. Configure redirect URI
# 4. Grant Mail.Read permissions

class GraphAttachmentDownloader:
    """Download attachments using Microsoft Graph API"""
    
    def __init__(self, client_id: str, client_secret: str, tenant_id: str = "common"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    def get_access_token_device_flow(self):
        """Get access token using device code flow (user-friendly)"""
        # Step 1: Request device code
        device_code_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/devicecode"
        
        data = {
            'client_id': self.client_id,
            'scope': 'https://graph.microsoft.com/Mail.Read offline_access'
        }
        
        response = requests.post(device_code_url, data=data)
        device_info = response.json()
        
        print(f"🔐 Please visit: {device_info['verification_uri']}")
        print(f"📱 Enter code: {device_info['user_code']}")
        print("⏳ Waiting for authentication...")
        
        # Step 2: Poll for token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        poll_data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'client_id': self.client_id,
            'device_code': device_info['device_code']
        }
        
        import time
        while True:
            time.sleep(device_info['interval'])
            token_response = requests.post(token_url, data=poll_data)
            token_result = token_response.json()
            
            if 'access_token' in token_result:
                self.access_token = token_result['access_token']
                print("✅ Authentication successful!")
                return True
            elif token_result.get('error') == 'authorization_pending':
                continue
            else:
                print(f"❌ Authentication failed: {token_result.get('error_description')}")
                return False
    
    def get_sent_emails_with_attachments(self, days_back: int = 30):
        """Get sent emails with attachments using Graph API"""
        if not self.access_token:
            print("❌ No access token. Please authenticate first.")
            return []
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Calculate date filter
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Query sent emails with attachments
        url = f"{self.base_url}/me/mailFolders/SentItems/messages"
        params = {
            '$filter': f"sentDateTime ge {since_date} and hasAttachments eq true",
            '$select': 'id,subject,sentDateTime,hasAttachments',
            '$orderby': 'sentDateTime desc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            emails = response.json().get('value', [])
            print(f"📧 Found {len(emails)} sent emails with attachments")
            return emails
        else:
            print(f"❌ Failed to get emails: {response.status_code} - {response.text}")
            return []
    
    def download_attachments(self, emails: list, output_dir: str):
        """Download attachments from emails"""
        if not emails:
            return 0
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        downloaded_count = 0
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        for email in emails:
            try:
                subject = email.get('subject', 'No Subject')
                sent_date = email.get('sentDateTime', '')
                email_id = email['id']
                
                # Create folder for this email
                safe_subject = re.sub(r'[^\w\s-]', '', subject).strip()[:50]
                safe_subject = re.sub(r'[-\s]+', '_', safe_subject)
                
                try:
                    date_obj = datetime.fromisoformat(sent_date.replace('Z', '+00:00'))
                    date_prefix = date_obj.strftime("%Y%m%d_%H%M%S")
                except:
                    date_prefix = "unknown_date"
                
                email_folder = Path(output_dir) / f"{date_prefix}_{safe_subject}"
                email_folder.mkdir(exist_ok=True)
                
                print(f"📧 Processing: {subject}")
                
                # Get attachments for this email
                attachments_url = f"{self.base_url}/me/messages/{email_id}/attachments"
                response = requests.get(attachments_url, headers=headers)
                
                if response.status_code == 200:
                    attachments = response.json().get('value', [])
                    
                    for attachment in attachments:
                        if attachment['@odata.type'] == '#microsoft.graph.fileAttachment':
                            filename = attachment['name']
                            content_bytes = base64.b64decode(attachment['contentBytes'])
                            
                            filepath = email_folder / filename
                            
                            # Handle duplicates
                            counter = 1
                            original_filepath = filepath
                            while filepath.exists():
                                name, ext = os.path.splitext(original_filepath)
                                filepath = Path(f"{name}_{counter}{ext}")
                                counter += 1
                            
                            # Save attachment
                            with open(filepath, 'wb') as f:
                                f.write(content_bytes)
                            
                            print(f"📎 Downloaded: {filepath}")
                            downloaded_count += 1
                
            except Exception as e:
                print(f"❌ Error processing email '{subject}': {e}")
                continue
        
        return downloaded_count

def main():
    """Demo of Graph API setup requirements"""
    print("🌐 Microsoft Graph API Attachment Downloader")
    print("=" * 50)
    print()
    print("📋 Setup Requirements:")
    print("1. Register an Azure app at https://portal.azure.com")
    print("2. Note down the Application (client) ID")
    print("3. Create a client secret")
    print("4. Add redirect URI: http://localhost")
    print("5. Grant 'Mail.Read' permission")
    print("6. Update this script with your client_id and client_secret")
    print()
    print("🔧 This approach is more reliable than IMAP for Outlook.com accounts")
    print("   but requires additional Azure setup.")

if __name__ == "__main__":
    main()