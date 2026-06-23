# This script demonstrates how to authenticate to Microsoft Graph API
# this script works 
import msal
import requests
from env_vars import CLIENT_ID

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
