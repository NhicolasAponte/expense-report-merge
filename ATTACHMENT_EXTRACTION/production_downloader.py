#!/usr/bin/env python3
"""
Production-Ready Batch Downloader for Large Email Datasets

FEATURES:
- Token refresh handling
- API rate limit respect
- Resume capability
- Progress tracking
- Size filtering
- Concurrent downloads
- Error recovery
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def add_production_methods_to_extractor():
    """
    Add these methods to your existing ModernWorkEmailExtractor class
    """
    
    def download_attachments_production(self, emails, output_dir, max_workers=5, 
                                      max_file_size_mb=50, resume=True):
        """Production-grade attachment downloader"""
        
        start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        progress_file = output_path / "download_progress.json"
        completed_emails = set()
        
        if resume and progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                    completed_emails = set(progress_data.get('completed_emails', []))
                logger.info(f"🔄 Resuming: {len(completed_emails)} emails already processed")
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        
        emails_to_process = [e for e in emails if e['id'] not in completed_emails]
        total_emails = len(emails)
        remaining_emails = len(emails_to_process)
        
        logger.info(f"📊 Processing {remaining_emails}/{total_emails} emails with {max_workers} workers")
        
        # Statistics tracking
        stats = {
            'downloaded': 0,
            'failed': 0,
            'skipped_large': 0,
            'total_size_mb': 0,
            'start_time': start_time
        }
        stats_lock = threading.Lock()
        
        # Process in batches to handle token refresh
        batch_size = 100  # Process 100 emails before checking token
        
        for batch_start in range(0, len(emails_to_process), batch_size):
            batch_end = min(batch_start + batch_size, len(emails_to_process))
            batch = emails_to_process[batch_start:batch_end]
            
            logger.info(f"📦 Processing batch {batch_start//batch_size + 1}: emails {batch_start+1}-{batch_end}")
            
            # Check and refresh token if needed
            self._ensure_valid_token()
            
            # Process batch concurrently
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_email = {
                    executor.submit(
                        self._download_email_attachments_safe,
                        email, output_path, max_file_size_mb * 1024 * 1024, 
                        batch_start + i + 1, total_emails
                    ): email for i, email in enumerate(batch)
                }
                
                for future in as_completed(future_to_email):
                    email = future_to_email[future]
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout per email
                        
                        with stats_lock:
                            stats['downloaded'] += result.get('downloaded', 0)
                            stats['failed'] += result.get('failed', 0)
                            stats['skipped_large'] += result.get('skipped_large', 0)
                            stats['total_size_mb'] += result.get('size_mb', 0)
                        
                        completed_emails.add(email['id'])
                        
                        # Save progress every 25 completions
                        if len(completed_emails) % 25 == 0:
                            self._save_progress(progress_file, completed_emails, stats)
                            self._log_progress(stats, len(completed_emails), total_emails)
                        
                    except Exception as e:
                        logger.error(f"❌ Email processing failed: {e}")
                        with stats_lock:
                            stats['failed'] += 1
            
            # Rate limiting: small delay between batches
            time.sleep(1)
        
        # Final save and report
        self._save_progress(progress_file, completed_emails, stats)
        return self._generate_final_report(stats, len(completed_emails), total_emails)
    
    def _ensure_valid_token(self):
        """Check token validity and refresh if needed"""
        try:
            # Simple test call to check token validity
            import requests
            response = requests.get(
                f"{self.graph_endpoint}/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )
            
            if response.status_code == 401:
                logger.info("🔄 Token expired, refreshing...")
                if not self.authenticate():
                    raise Exception("Failed to refresh authentication")
                    
        except Exception as e:
            logger.warning(f"Token validation issue: {e}")
    
    def _download_email_attachments_safe(self, email, output_path, max_file_size, 
                                       email_index, total_emails):
        """Safely download attachments for a single email with error handling"""
        
        result = {'downloaded': 0, 'failed': 0, 'skipped_large': 0, 'size_mb': 0}
        
        try:
            email_id = email["id"]
            subject = email.get("subject", "No_Subject")[:50]
            
            # Get attachments with retry logic
            attachments = self._get_attachments_with_retry(email_id, retries=3)
            if not attachments:
                return result
            
            # Create email folder
            try:
                email_date = datetime.fromisoformat(email["receivedDateTime"].replace("Z", "+00:00"))
                email_date_str = email_date.strftime("%Y%m%d_%H%M%S")
            except:
                email_date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
            email_folder = output_path / f"{email_date_str}_{safe_subject}"
            email_folder.mkdir(exist_ok=True)
            
            # Download each attachment
            for attachment in attachments:
                try:
                    if attachment.get("@odata.type") != "#microsoft.graph.fileAttachment":
                        continue
                    
                    filename = attachment.get("name", f"attachment_{email_index}")
                    file_size = attachment.get("size", 0)
                    
                    # Size check
                    if file_size > max_file_size:
                        logger.debug(f"⏭️  Skipping large file: {filename} ({file_size/(1024*1024):.1f}MB)")
                        result['skipped_large'] += 1
                        continue
                    
                    # File type filter (optional)
                    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'}
                    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
                        continue
                    
                    content_bytes = attachment.get("contentBytes", "")
                    if content_bytes:
                        import base64
                        content = base64.b64decode(content_bytes)
                        
                        # Clean filename and save
                        clean_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                        filepath = email_folder / clean_filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        result['downloaded'] += 1
                        result['size_mb'] += len(content) / (1024 * 1024)
                        
                        if result['downloaded'] % 100 == 0:
                            logger.info(f"📁 Downloaded {result['downloaded']} files from email {email_index}/{total_emails}")
                
                except Exception as e:
                    logger.debug(f"Attachment download failed: {e}")
                    result['failed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Email processing failed for {email_index}: {e}")
            result['failed'] += 1
            return result
    
    def _get_attachments_with_retry(self, email_id, retries=3):
        """Get attachments with retry logic for robustness"""
        import requests
        
        for attempt in range(retries):
            try:
                url = f"{self.graph_endpoint}/me/messages/{email_id}/attachments"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    return response.json().get("value", [])
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.info(f"⏳ Rate limited, waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.warning(f"API error {response.status_code} for email {email_id}")
                    return []
                    
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.debug(f"Retry {attempt + 1} in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to get attachments after {retries} attempts: {e}")
        
        return []
    
    def _log_progress(self, stats, completed, total):
        """Log detailed progress information"""
        elapsed = time.time() - stats['start_time']
        rate = stats['downloaded'] / elapsed if elapsed > 0 else 0
        
        if stats['downloaded'] > 0:
            eta_seconds = (10000 - stats['downloaded']) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            logger.info(f"📈 Progress: {completed}/{total} emails | "
                       f"{stats['downloaded']} files | "
                       f"{rate:.1f} files/sec | "
                       f"ETA: {eta_minutes:.0f}min | "
                       f"{stats['total_size_mb']:.1f}MB")
    
    def _save_progress(self, progress_file, completed_emails, stats):
        """Save progress for resume capability"""
        try:
            progress_data = {
                'completed_emails': list(completed_emails),
                'timestamp': datetime.now().isoformat(),
                'stats': stats
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def _generate_final_report(self, stats, completed_emails, total_emails):
        """Generate comprehensive completion report"""
        elapsed_hours = (time.time() - stats['start_time']) / 3600
        
        report = {
            'total_emails': total_emails,
            'completed_emails': completed_emails,
            'downloaded_files': stats['downloaded'],
            'failed_downloads': stats['failed'],
            'skipped_large_files': stats['skipped_large'],
            'total_size_gb': round(stats['total_size_mb'] / 1024, 2),
            'elapsed_hours': round(elapsed_hours, 2),
            'download_rate_files_per_hour': round(stats['downloaded'] / elapsed_hours, 0) if elapsed_hours > 0 else 0,
            'success_rate': round((stats['downloaded'] / max(stats['downloaded'] + stats['failed'], 1)) * 100, 1)
        }
        
        logger.info("🎉 DOWNLOAD COMPLETE!")
        logger.info(f"📊 Final Stats:")
        logger.info(f"   Emails processed: {report['completed_emails']}/{report['total_emails']}")
        logger.info(f"   Files downloaded: {report['downloaded_files']}")
        logger.info(f"   Total size: {report['total_size_gb']} GB")
        logger.info(f"   Time taken: {report['elapsed_hours']} hours")
        logger.info(f"   Success rate: {report['success_rate']}%")
        
        return report

# Usage example in your main script:
# Simply replace the existing download_attachments call with:
# downloaded_count = extractor.download_attachments_production(
#     emails=emails,
#     output_dir=account_output_dir,
#     max_workers=5,
#     max_file_size_mb=50,
#     resume=True
# )