#!/usr/bin/env python3
"""
Gmail Attachment Downloader - Final Usage Guide
This demonstrates how to customize and use the attachment extraction system.
"""

from ATTACHMENT_EXTRACTION.gmail_extraction.download_gmail_attachments import GmailAttachmentDownloader
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import GMAIL_ADDRESS, GMAIL_PASSWORD, OUTPUT_DIR
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Demonstrate different usage scenarios for the attachment downloader"""
    
    print("📧 Gmail Attachment Downloader - Usage Guide")
    print("=" * 60)
    
    # Create downloader instance
    downloader = GmailAttachmentDownloader(GMAIL_ADDRESS, GMAIL_PASSWORD)
    
    print("\n🎯 Available Usage Scenarios:")
    print("1. Download ALL attachments from recent emails")
    print("2. Download expense-related attachments")
    print("3. Download invoice/receipt attachments")
    print("4. Download resume/job-related attachments")
    print("5. Download attachments from specific time period")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        # Download all attachments from last 30 days
        print("\n📅 Downloading ALL attachments from last 30 days...")
        downloader.run(
            days_back=30,
            search_subject=None,
            output_dir=f"{OUTPUT_DIR}/all_recent"
        )
    
    elif choice == "2":
        # Download expense-related attachments
        print("\n💰 Downloading expense-related attachments...")
        keywords = ["expense", "receipt", "reimbursement", "cost"]
        for keyword in keywords:
            print(f"   Searching for: {keyword}")
            downloader.run(
                days_back=365,
                search_subject=keyword,
                output_dir=f"{OUTPUT_DIR}/expenses/{keyword}"
            )
    
    elif choice == "3":
        # Download invoice/receipt attachments
        print("\n🧾 Downloading invoice/receipt attachments...")
        keywords = ["invoice", "receipt", "bill", "payment"]
        for keyword in keywords:
            print(f"   Searching for: {keyword}")
            downloader.run(
                days_back=365,
                search_subject=keyword,
                output_dir=f"{OUTPUT_DIR}/invoices/{keyword}"
            )
    
    elif choice == "4":
        # Download resume/job-related attachments
        print("\n💼 Downloading resume/job-related attachments...")
        keywords = ["resume", "cv", "cover letter", "application"]
        for keyword in keywords:
            print(f"   Searching for: {keyword}")
            downloader.run(
                days_back=365,
                search_subject=keyword,
                output_dir=f"{OUTPUT_DIR}/job_applications/{keyword.replace(' ', '_')}"
            )
    
    elif choice == "5":
        # Custom time period
        try:
            days = int(input("Enter number of days to look back: "))
            subject_filter = input("Enter subject filter (or press Enter for all): ").strip()
            if not subject_filter:
                subject_filter = None
            
            print(f"\n📅 Downloading attachments from last {days} days...")
            downloader.run(
                days_back=days,
                search_subject=subject_filter,
                output_dir=f"{OUTPUT_DIR}/custom_{days}_days"
            )
        except ValueError:
            print("❌ Invalid number of days")
            return
    
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✅ Download completed!")
    print(f"📁 Check your files in: {OUTPUT_DIR}")
    
    # Show some usage tips
    print("\n💡 Usage Tips:")
    print("• Files are organized by email date and subject")
    print("• Duplicate files get numbered automatically")
    print("• Use subject filters to find specific types of attachments")
    print("• Adjust days_back to search further into the past")
    print("• Check the logs above for any issues or errors")

if __name__ == "__main__":
    main()