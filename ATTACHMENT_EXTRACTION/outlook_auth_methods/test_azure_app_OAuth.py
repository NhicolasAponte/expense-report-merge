#!/usr/bin/env python3
"""
Azure App OAuth Test - MSAL Library Device Flow Authentication

AUTHENTICATION METHOD:
- OAuth 2.0 Device Code Flow using MSAL (Microsoft Authentication Library)
- Modern authentication for personal Microsoft accounts
- Uses official Microsoft authentication library

WHAT IT DOES:
- Demonstrates OAuth2 authentication using MSAL library
- Implements device code flow for personal accounts
- Tests Microsoft Graph API access
- Validates authentication with profile information retrieval

MICROSOFT REQUIREMENTS:
1. Azure App Registration:
   - Register app at https://portal.azure.com
   - Application type: Public client/native
   - Supported account types: Personal Microsoft accounts only
   - Required permissions: User.Read, Mail.Read
   - No redirect URI needed for device flow
   - Copy Application (client) ID to CLIENT_ID variable

2. Environment Variables:
   - CLIENT_ID: Your Azure app registration client ID
   - Set in .env file or environment variables

ADVANTAGES:
- Uses official Microsoft MSAL library
- Proper token caching and refresh handling
- Optimized for personal accounts
- Standard OAuth2 implementation
- Built-in error handling

AUTHENTICATION FLOW:
1. Create MSAL PublicClientApplication
2. Initiate device code flow
3. Display user code and verification URL
4. User completes authentication on any device
5. Acquire access token automatically
6. Test Graph API access

SETUP STEPS:
1. Register app in Azure portal (https://portal.azure.com)
2. Configure for personal accounts (/consumers endpoint)
3. Add CLIENT_ID to .env file
4. Install MSAL: pip install msal
5. Run script and follow authentication prompts

USE CASES:
- Production applications requiring personal account access
- Scripts needing proper token management
- Applications requiring MSAL library integration
- Scenarios needing Microsoft's official auth library

DEPENDENCIES:
- msal: Microsoft Authentication Library
- requests: HTTP client for API calls
"""

# This script demonstrates how to authenticate to Microsoft Graph API
# this script works 
import msal
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import CLIENT_ID

# Microsoft Graph endpoint
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me"

# Create a public client app (no secret needed)
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority="https://login.microsoftonline.com/consumers"  # 'consumers' = personal Microsoft accounts
)

# The scope defines what access you’re requesting
scopes = ["User.Read", "Mail.Read"]

# Use device code flow (lets you log in in your browser)
flow = app.initiate_device_flow(scopes=scopes)
if "user_code" not in flow:
    raise Exception("Failed to create device flow")

print(flow["message"])  # tells you where to go (https://microsoft.com/devicelogin)
result = app.acquire_token_by_device_flow(flow)

# Check for success
if "access_token" in result:
    print("\n✅ Authentication successful!")
    print("Access token acquired.\n")

    # Test call to Microsoft Graph: get your user profile
    response = requests.get(
        GRAPH_API_ENDPOINT,
        headers={"Authorization": f"Bearer {result['access_token']}"}
    )

    print("👤 Graph API response:")
    print(response.json())

else:
    print(f"\n❌ Authentication failed: {result.get('error_description')}")
