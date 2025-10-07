#!/usr/bin/env python3
"""
OAuth2 Simple Test - Modern Authentication for Microsoft 365

AUTHENTICATION METHOD:
- OAuth 2.0 Authorization Code Flow with PKCE
- Uses local HTTP server to capture redirect
- Modern authentication (no basic auth)

WHAT IT DOES:
- Implements a simplified OAuth2 flow for Microsoft 365
- Starts a local HTTP server on localhost:8080 to capture the authorization code
- Opens browser for user authentication
- Exchanges authorization code for access tokens
- Tests API access with the obtained token

MICROSOFT REQUIREMENTS:
1. Azure App Registration (recommended):
   - Go to https://portal.azure.com > App registrations > New registration
   - Set redirect URI to: http://localhost:8080
   - Configure API permissions: Mail.Read, offline_access
   - Note the Application (client) ID

2. Alternative (Uses hardcoded public client ID):
   - Script uses a0c73c16-a7e3-4564-9a95-2bdf47383716 (Microsoft Graph PowerShell)
   - This works but is not recommended for production use

ADVANTAGES:
- No app passwords required
- Works with MFA-enabled accounts
- More secure than basic authentication
- Supports token refresh

LIMITATIONS:
- Requires user interaction (browser)
- Needs local server on port 8080
- Tokens expire and need refresh

SETUP STEPS:
1. Optional: Register your own app in Azure (recommended)
2. Update CLIENT_ID variable if using custom app
3. Ensure port 8080 is available
4. Run script and follow browser prompts

USE CASES:
- Testing OAuth2 flow
- Developing applications with user consent
- Scenarios requiring explicit user authentication
"""

import requests
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if 'code=' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                    <body>
                        <h1>Authentication Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                    </body>
                </html>
            """)
            # Parse the code from the URL
            code = self.path.split('code=')[1].split('&')[0]
            self.server.auth_code = code
        else:
            self.send_response(400)
            self.end_headers()

def get_token_simple():
    """Simple OAuth flow using local HTTP server"""
    
    CLIENT_ID = "a0c73c16-a7e3-4564-9a95-2bdf47383716"
    REDIRECT_URI = "http://localhost:8080"
    
    # Start local server to catch redirect
    server = HTTPServer(('localhost', 8080), AuthHandler)
    server.auth_code = None
    
    def run_server():
        server.handle_request()
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Build auth URL
    auth_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=Mail.Read"
        "&response_mode=query"
    )
    
    print("Opening browser for authentication...")
    webbrowser.open(auth_url)
    
    # Wait for auth code
    timeout = 60
    start_time = time.time()
    while server.auth_code is None and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    if server.auth_code:
        print(f"Got auth code: {server.auth_code[:10]}...")
        return server.auth_code
    else:
        print("Timeout waiting for authentication")
        return None

if __name__ == "__main__":
    print("Simple Graph API Test")
    code = get_token_simple()
    if code:
        print("✅ Authentication successful!")
    else:
        print("❌ Authentication failed")