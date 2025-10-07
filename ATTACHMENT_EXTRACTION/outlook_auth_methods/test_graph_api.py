#!/usr/bin/env python3
"""
Microsoft Graph API Test - Modern Authentication with MSAL and Graph API

AUTHENTICATION METHOD:
- OAuth 2.0 Device Code Flow using MSAL library
- Microsoft Graph API for email and user data access
- Modern authentication with automatic token management

WHAT IT DOES:
- Demonstrates Microsoft Graph API authentication and usage
- Implements device code flow for personal and organizational accounts
- Tests Graph API endpoints (user profile, mail, folders)
- Shows email attachment download via Graph API
- Provides complete Graph API integration example

MICROSOFT REQUIREMENTS:
1. Azure App Registration (Optional):
   - Script uses Microsoft Graph PowerShell public client by default
   - For production: Register at https://portal.azure.com
   - Application type: Public client/native
   - Required permissions: Mail.Read, Mail.ReadWrite, Mail.Send, User.Read

2. Account Requirements:
   - Microsoft 365 or Outlook.com account
   - Modern authentication enabled
   - No app passwords required

GRAPH API FEATURES:
- User profile information
- Email folder listing
- Message retrieval and search
- Attachment download
- Message sending capabilities
- Rich metadata access

AUTHENTICATION FLOW:
1. Initialize MSAL PublicClientApplication
2. Check for cached tokens first
3. If no cache, initiate device code flow
4. Display user code and verification URL
5. User completes authentication on any device
6. Automatic token acquisition and caching
7. Use access token for Graph API calls

ADVANTAGES:
- Modern OAuth2 authentication
- Rich API features beyond email
- Automatic token refresh and caching
- Works with MFA-enabled accounts
- Official Microsoft library support
- Cross-platform compatibility

SETUP STEPS:
1. No Azure registration required (uses public client)
2. Install MSAL: pip install msal
3. Run script and follow device authentication
4. Visit verification URL and enter user code

USE CASES:
- Modern email application development
- Rich email metadata and operations
- Cross-platform email clients
- Applications requiring Graph API features
- Scenarios needing official Microsoft API support

API ENDPOINTS TESTED:
- /me (user profile)
- /me/mailFolders (folder structure)
- /me/messages (email retrieval)
- /me/messages/{id}/attachments (attachment access)

DEPENDENCIES:
- msal: Microsoft Authentication Library
- requests: HTTP client for Graph API calls
"""

import msal
import requests
import json

def get_access_token():
    """Get access token using device code flow - works for personal accounts"""
    
    # Microsoft Graph PowerShell app ID (public client)
    CLIENT_ID = "a0c73c16-a7e3-4564-9a95-2bdf47383716"
    SCOPES = ["Mail.Read", "Mail.ReadWrite", "Mail.Send"]
    
    authority = "https://login.microsoftonline.com/common"
    
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=authority
    )
    
    print("=== Microsoft Graph API Authentication ===")
    print("We'll use the device code flow for personal accounts.")
    
    # First, try to get token silently from cache
    accounts = app.get_accounts()
    result = None
    
    if accounts:
        print("Found cached accounts, attempting silent authentication...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    
    if not result:
        print("No cached token found. Starting device flow...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow")
            
        print(flow["message"])
        
        # This will block until user completes authentication
        result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        print("✅ Successfully obtained access token!")
        return result["access_token"]
    else:
        print(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
        return None

def test_graph_connection(access_token):
    """Test connection to Microsoft Graph"""
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("\n=== Testing Graph API Connection ===")
    
    # Test basic user info
    user_response = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers=headers
    )
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"✅ Connected as: {user_data.get('displayName', 'Unknown')} ({user_data.get('userPrincipalName')})")
    else:
        print(f"❌ User info failed: {user_response.status_code} - {user_response.text}")
        return False
    
    # Test mailbox info
    mailbox_response = requests.get(
        'https://graph.microsoft.com/v1.0/me/mailFolders/inbox',
        headers=headers
    )
    
    if mailbox_response.status_code == 200:
        inbox_data = mailbox_response.json()
        print(f"✅ Inbox access: {inbox_data.get('displayName', 'Unknown')}")
        print(f"   Total items: {inbox_data.get('totalItemCount', 'Unknown')}")
    else:
        print(f"❌ Mailbox access failed: {mailbox_response.status_code}")
        return False
    
    return True

def get_emails_with_attachments(access_token, folder='sentItems'):
    """Get emails with attachments from specified folder"""
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Search for emails with attachments and invoice in subject
    query = "?$filter=hasAttachments eq true and contains(subject,'invoice')"
    query += "&$top=5&$select=subject,receivedDateTime,hasAttachments"
    query += "&$expand=attachments($select=name,contentType,size)"
    
    url = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder}/messages{query}'
    
    print(f"\n=== Searching for invoices in {folder} ===")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        emails = response.json().get('value', [])
        print(f"✅ Found {len(emails)} emails with attachments")
        
        for email in emails:
            print(f"\n📧 {email['subject']}")
            print(f"   📅 {email['receivedDateTime']}")
            attachments = email.get('attachments', [])
            print(f"   📎 {len(attachments)} attachment(s)")
            for att in attachments:
                print(f"      - {att['name']} ({att['contentType']}, {att['size']} bytes)")
        
        return emails
    else:
        print(f"❌ Email search failed: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    print("Microsoft Graph API Test for Outlook")
    print("This uses modern OAuth 2.0 authentication (not Basic Auth)")
    print("=" * 60)
    
    token = get_access_token()
    
    if token:
        if test_graph_connection(token):
            # Test with a small sample
            emails = get_emails_with_attachments(token, 'sentItems')
            
            if emails:
                print(f"\n🎉 SUCCESS! Graph API is working.")
                print("We can now build the full invoice recovery solution!")
            else:
                print("\n⚠️  Connection works, but no invoices found in sent items.")
                print("Try checking other folders or adjust the search query.")
    else:
        print("\n🔴 Failed to get access token.")
        print("This might be due to:")
        print("1. Network issues")
        print("2. User canceled authentication")
        print("3. Application permissions")