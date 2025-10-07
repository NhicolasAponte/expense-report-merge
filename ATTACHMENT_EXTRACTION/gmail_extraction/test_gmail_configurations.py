#!/usr/bin/env python3
"""
Test Gmail attachment downloader with different configurations
"""

from ATTACHMENT_EXTRACTION.gmail_extraction.download_gmail_attachments import GmailAttachmentDownloader
from env_vars import GMAIL_ADDRESS, GMAIL_PASSWORD, OUTPUT_DIR
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_different_configurations():
    """Test different search configurations"""
    
    downloader = GmailAttachmentDownloader(GMAIL_ADDRESS, GMAIL_PASSWORD)
    
    print("🧪 Testing Different Search Configurations")
    print("=" * 50)
    
    # Test 1: Last 7 days
    print("\n📅 Test 1: Last 7 days")
    success = downloader.run(days_back=7, search_subject=None, output_dir=f"{OUTPUT_DIR}/last_7_days")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 2: Last 90 days
    print("\n📅 Test 2: Last 90 days")
    success = downloader.run(days_back=90, search_subject=None, output_dir=f"{OUTPUT_DIR}/last_90_days")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 3: Filter by subject containing "resume"
    print("\n🔍 Test 3: Emails with 'resume' in subject")
    success = downloader.run(days_back=365, search_subject="resume", output_dir=f"{OUTPUT_DIR}/resume_emails")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 4: Filter by subject containing "invoice"
    print("\n🔍 Test 4: Emails with 'invoice' in subject")
    success = downloader.run(days_back=365, search_subject="invoice", output_dir=f"{OUTPUT_DIR}/invoice_emails")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_different_configurations()