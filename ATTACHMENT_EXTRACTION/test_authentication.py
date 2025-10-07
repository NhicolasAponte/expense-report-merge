"""
AUTHENTICATION TEST SCRIPT

PURPOSE: Test OAuth 2.0 authentication and basic Microsoft Graph API access
SCOPE: Authentication only - NO downloading or processing
OUTPUT: Verification of credentials and permissions

This script will:
1. Test Azure app registration credentials
2. Authenticate using OAuth 2.0 Device Code Flow
3. Verify Graph API access
4. List mailboxes and basic info
5. Display authentication status

REQUIREMENTS:
- WORK_CLIENT_ID and WORK_TENANT_ID configured in .env
- Admin consent granted for the Azure app
- MSAL package installed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check for MSAL availability
try:
    import msal
    import requests
    MSAL_AVAILABLE = True
    logger.info("✅ MSAL library available")
except ImportError:
    logger.error("❌ MSAL not installed. Run: pip install msal")
    sys.exit(1)

from env_config import CLIENT_ID, TENANT_ID, WORK_EMAIL_ADDRESS

# ================================
# CONFIGURATION
# ================================

# Microsoft Graph API endpoints
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/offline_access"
]

class AuthenticationTester:
    """Test OAuth 2.0 authentication and basic Graph API access"""
    
    def __init__(self, client_id: str, tenant_id: str):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.access_token = None
        
        # Create MSAL public client app
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
    def test_authentication(self) -> bool:
        """Test OAuth 2.0 authentication using device code flow"""
        logger.info("🔐 Starting OAuth 2.0 authentication test...")
        
        try:
            # Check for cached tokens first
            accounts = self.app.get_accounts()
            if accounts:
                logger.info(f"📋 Found {len(accounts)} cached account(s)")
                for account in accounts:
                    logger.info(f"   - {account.get('username', 'Unknown')}")
                
                # Try to get token silently
                result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
                if result and 'access_token' in result:
                    logger.info("✅ Using cached authentication token")
                    self.access_token = result['access_token']
                    return True
            
            # No cached token, use device code flow
            logger.info("🔗 Starting device code authentication flow...")
            
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                logger.error("❌ Failed to create device flow")
                return False
            
            # Display device code instructions
            print("\n" + "="*60)
            print("🔐 AUTHENTICATION REQUIRED")
            print("="*60)
            print(f"📱 Open: {flow['verification_uri']}")
            print(f"🔑 Enter code: {flow['user_code']}")
            print("⏱️  You have 15 minutes to complete authentication")
            print("="*60)
            
            # Wait for user to complete authentication
            result = self.app.acquire_token_by_device_flow(flow)
            
            if 'access_token' in result:
                logger.info("✅ Authentication successful!")
                self.access_token = result['access_token']
                return True
            else:
                logger.error(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_graph_api_access(self) -> bool:
        """Test basic Microsoft Graph API access"""
        if not self.access_token:
            logger.error("❌ No access token available")
            return False
        
        logger.info("🌐 Testing Microsoft Graph API access...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test 1: Get user profile
            logger.info("📝 Testing user profile access...")
            response = requests.get(f"{GRAPH_ENDPOINT}/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info("✅ User profile access successful")
                logger.info(f"   - Name: {user_data.get('displayName', 'Unknown')}")
                logger.info(f"   - Email: {user_data.get('mail', user_data.get('userPrincipalName', 'Unknown'))}")
            else:
                logger.error(f"❌ User profile access failed: {response.status_code}")
                logger.error(f"   Error: {response.text}")
                return False
            
            # Test 2: Check mailbox access
            logger.info("📧 Testing mailbox access...")
            response = requests.get(f"{GRAPH_ENDPOINT}/me/mailFolders", headers=headers)
            
            if response.status_code == 200:
                folders = response.json()
                logger.info("✅ Mailbox access successful")
                logger.info(f"   - Found {len(folders.get('value', []))} mail folders")
                
                # List some key folders
                for folder in folders.get('value', [])[:5]:
                    logger.info(f"   - {folder.get('displayName', 'Unknown')}")
            else:
                logger.error(f"❌ Mailbox access failed: {response.status_code}")
                logger.error(f"   Error: {response.text}")
                return False
            
            # Test 3: Check message count (without downloading)
            logger.info("📊 Testing message count access...")
            response = requests.get(
                f"{GRAPH_ENDPOINT}/me/messages",
                headers=headers,
                params={'$top': 1, '$select': 'id,subject,receivedDateTime'}
            )
            
            if response.status_code == 200:
                messages = response.json()
                logger.info("✅ Message access successful")
                if messages.get('value'):
                    sample_msg = messages['value'][0]
                    logger.info(f"   - Sample message: {sample_msg.get('subject', 'No subject')}")
                    logger.info(f"   - Received: {sample_msg.get('receivedDateTime', 'Unknown')}")
                else:
                    logger.info("   - No messages found in mailbox")
            else:
                logger.error(f"❌ Message access failed: {response.status_code}")
                logger.error(f"   Error: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Graph API test error: {str(e)}")
            return False
    
    def run_full_test(self) -> bool:
        """Run complete authentication and access test"""
        logger.info(f"🚀 Starting authentication test at {datetime.now()}")
        logger.info(f"📧 Target email: {WORK_EMAIL_ADDRESS}")
        
        # Step 1: Test authentication
        if not self.test_authentication():
            logger.error("❌ Authentication test failed")
            return False
        
        # Step 2: Test Graph API access
        if not self.test_graph_api_access():
            logger.error("❌ Graph API access test failed")
            return False
        
        logger.info("🎉 All tests passed! Authentication and access verified.")
        return True

def main():
    """Main function to run authentication tests"""
    print("🔍 AUTHENTICATION & ACCESS TEST")
    print("="*50)
    
    # Validate configuration
    if not CLIENT_ID or CLIENT_ID == "your-azure-app-client-id":
        logger.error("❌ CLIENT_ID not configured properly")
        logger.error("Please update WORK_CLIENT_ID in .env file")
        return False
    
    if not TENANT_ID or TENANT_ID == "NEED_FROM_IT_ADMIN":
        logger.error("❌ TENANT_ID not configured properly")
        logger.error("Please update WORK_TENANT_ID in .env file")
        return False
    
    logger.info(f"📋 Configuration:")
    logger.info(f"   - Client ID: {CLIENT_ID[:8]}...")
    logger.info(f"   - Tenant ID: {TENANT_ID[:8]}...")
    logger.info(f"   - Work Email: {WORK_EMAIL_ADDRESS}")
    
    # Run authentication test
    tester = AuthenticationTester(CLIENT_ID, TENANT_ID)
    success = tester.run_full_test()
    
    if success:
        print("\n" + "="*50)
        print("✅ AUTHENTICATION TEST SUCCESSFUL!")
        print("📧 You can now use the modern_work_extractor.py")
        print("🚀 Ready to download attachments when needed")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ AUTHENTICATION TEST FAILED!")
        print("🔧 Please check the error messages above")
        print("📋 Common issues:")
        print("   - Admin consent not granted")
        print("   - Incorrect CLIENT_ID or TENANT_ID")
        print("   - Missing API permissions")
        print("="*50)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)