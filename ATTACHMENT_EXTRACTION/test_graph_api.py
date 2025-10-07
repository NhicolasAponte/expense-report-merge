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