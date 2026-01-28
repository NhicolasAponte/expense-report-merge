#!/usr/bin/env python3
"""
Debug script to check Azure app permissions and access
"""

import requests
import msal
from env_config import CLIENT_ID, TENANT_ID, WORK_EMAIL_ADDRESS

def check_permissions():
    """Check what permissions and access we actually have"""
    
    # Create MSAL app
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=authority
    )
    
    # Try to get cached token
    accounts = app.get_accounts()
    if accounts:
        print("✅ Found cached authentication")
        result = app.acquire_token_silent(
            scopes=["https://graph.microsoft.com/Mail.Read"], 
            account=accounts[0]
        )
        
        if result and "access_token" in result:
            access_token = result["access_token"]
            print("✅ Got access token")
            
            # Test different API calls to see what works
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            print("\n🔍 Testing API Access...")
            
            # Test 1: Get user profile
            print("\n1. Testing user profile access...")
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_data = response.json()
                print(f"   User: {user_data.get('displayName')} ({user_data.get('mail', user_data.get('userPrincipalName'))})")
            else:
                print(f"   Error: {response.text}")
            
            # Test 2: List mail folders
            print("\n2. Testing mail folders access...")
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/users/{WORK_EMAIL_ADDRESS}/mailFolders",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                folders = response.json().get("value", [])
                print(f"   Found {len(folders)} folders:")
                for folder in folders[:5]:  # Show first 5
                    print(f"     - {folder.get('displayName')}")
            else:
                print(f"   Error: {response.text}")
            
            # Test 3: Try inbox access directly
            print("\n3. Testing inbox access...")
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/users/{WORK_EMAIL_ADDRESS}/mailFolders/inbox/messages",
                headers=headers,
                params={"$top": 1}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Inbox access successful!")
            else:
                print(f"   ❌ Inbox access failed: {response.text}")
            
            # Test 4: Try with /me endpoint instead
            print("\n4. Testing /me/messages access...")
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers=headers,
                params={"$top": 1}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ /me/messages access successful!")
            else:
                print(f"   ❌ /me/messages access failed: {response.text}")
        
        else:
            print("❌ Failed to get access token")
            if result:
                print(f"Error: {result.get('error_description', 'Unknown error')}")
            else:
                print("Error: No result returned from token request")
    
    else:
        print("❌ No cached authentication found. Please run the main script first to authenticate.")

if __name__ == "__main__":
    print("🔍 Azure App Permissions Diagnostic")
    print("=" * 50)
    check_permissions()