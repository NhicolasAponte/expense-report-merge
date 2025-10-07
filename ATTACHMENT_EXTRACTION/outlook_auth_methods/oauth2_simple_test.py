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