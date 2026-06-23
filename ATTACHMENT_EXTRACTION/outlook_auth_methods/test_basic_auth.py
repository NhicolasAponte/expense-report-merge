from exchangelib import Credentials, Account, DELEGATE
import sys
import os
# Add parent directory to path to import env_vars
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from env_vars import WORK_EMAIL_ADDRESS, WORK_PASSWORD
# Replace these with your personal Outlook credentials
email = WORK_EMAIL_ADDRESS
password = WORK_PASSWORD

try:
    credentials = Credentials(email, password)
    account = Account(
        primary_smtp_address=email,
        credentials=credentials,
        autodiscover=True,
        access_type=DELEGATE
    )

    print(f"✅ Authentication successful! Logged in as: {account.display_name}")
    print(f"📧 Inbox total items: {account.inbox.total_count}")

except Exception as e:
    print(f"❌ Authentication failed: {e}")
