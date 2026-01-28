#!/usr/bin/env python3
"""
Optimized Email Extractor - High Performance Version for Large Datasets

PERFORMANCE OPTIMIZATIONS:
- Concurrent downloads using threading
- Batch API requests
- Progress tracking with ETA
- Size limits and filtering
- Resume capability
- Memory-efficient processing
"""

import concurrent.futures
import threading
import time
from pathlib import Path
import json

# Add to the existing ModernWorkEmailExtractor class
class OptimizedAttachmentDownloader:
    """High-performance attachment downloader with concurrency and batching"""
    
    def __init__(self, access_token: str, graph_endpoint: str, max_workers: int = 5):
        self.access_token = access_token
        self.graph_endpoint = graph_endpoint
        self.max_workers = max_workers
        self.downloaded_count = 0
        self.failed_count = 0
        self.total_size = 0
        self.start_time = None
        self.lock = threading.Lock()
        
    def download_attachments_optimized(self, emails: List[Dict], output_dir: str, 
                                     max_file_size_mb: int = 50) -> Dict:
        """Download attachments with concurrent processing"""
        
        self.start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create progress tracking file
        progress_file = output_path / "download_progress.json"
        
        # Load existing progress if resuming
        completed_emails = set()
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                    completed_emails = set(progress_data.get('completed_emails', []))
                logger.info(f"Resuming: {len(completed_emails)} emails already processed")
            except:
                pass
        
        # Filter out already completed emails
        emails_to_process = [email for email in emails if email['id'] not in completed_emails]
        
        logger.info(f"Processing {len(emails_to_process)} emails with {self.max_workers} concurrent workers")
        logger.info(f"Maximum file size: {max_file_size_mb}MB")
        
        # Process emails concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single_email, 
                    email, 
                    output_path, 
                    max_file_size_mb * 1024 * 1024,
                    len(emails_to_process),
                    i + 1
                ): email for i, email in enumerate(emails_to_process)
            }
            
            for future in concurrent.futures.as_completed(futures):
                email = futures[future]
                try:
                    result = future.result()
                    if result['success']:
                        completed_emails.add(email['id'])
                        
                        # Update progress file every 10 completions
                        if len(completed_emails) % 10 == 0:
                            self._save_progress(progress_file, completed_emails)
                            
                except Exception as e:
                    logger.error(f"Failed to process email {email.get('subject', 'Unknown')}: {e}")
                    with self.lock:
                        self.failed_count += 1
        
        # Final progress save
        self._save_progress(progress_file, completed_emails)
        
        # Calculate final statistics
        elapsed_time = time.time() - self.start_time
        stats = {
            'total_emails': len(emails),
            'processed_emails': len(completed_emails),
            'downloaded_files': self.downloaded_count,
            'failed_downloads': self.failed_count,
            'total_size_mb': round(self.total_size / (1024 * 1024), 2),
            'elapsed_time_minutes': round(elapsed_time / 60, 2),
            'avg_time_per_email': round(elapsed_time / max(len(emails_to_process), 1), 2),
            'download_rate_files_per_minute': round(self.downloaded_count / (elapsed_time / 60), 2)
        }
        
        return stats
    
    def _process_single_email(self, email: Dict, output_path: Path, 
                            max_file_size: int, total_emails: int, email_index: int) -> Dict:
        """Process a single email and download its attachments"""
        
        try:
            email_id = email["id"]
            subject = email.get("subject", "No_Subject")
            
            # Get attachments
            url = f"{self.graph_endpoint}/me/messages/{email_id}/attachments"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return {'success': False, 'error': f"API error: {response.status_code}"}
            
            attachments_data = response.json()
            attachments = attachments_data.get("value", [])
            
            if not attachments:
                return {'success': True, 'downloaded': 0}
            
            # Create email folder
            try:
                email_date = datetime.fromisoformat(email["receivedDateTime"].replace("Z", "+00:00"))
                email_date_str = email_date.strftime("%Y%m%d_%H%M%S")
            except:
                email_date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            email_folder = output_path / f"{email_date_str}_{safe_subject}"
            email_folder.mkdir(exist_ok=True)
            
            # Download attachments
            downloaded_in_email = 0
            for attachment in attachments:
                try:
                    if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                        filename = attachment.get("name", f"attachment_{email_index}")
                        file_size = attachment.get("size", 0)
                        
                        # Skip large files
                        if file_size > max_file_size:
                            logger.warning(f"Skipping large file: {filename} ({file_size / (1024*1024):.1f}MB)")
                            continue
                        
                        # Skip if not PDF (optional filter)
                        if not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.xls', '.xlsx')):
                            continue
                        
                        content_bytes = attachment.get("contentBytes", "")
                        if content_bytes:
                            content = base64.b64decode(content_bytes)
                            
                            # Clean filename
                            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                            filepath = email_folder / filename
                            
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            
                            with self.lock:
                                self.downloaded_count += 1
                                self.total_size += len(content)
                                downloaded_in_email += 1
                                
                                # Progress reporting
                                if self.downloaded_count % 50 == 0:
                                    self._report_progress(email_index, total_emails)
                
                except Exception as e:
                    logger.error(f"Failed to download attachment {filename}: {e}")
                    with self.lock:
                        self.failed_count += 1
            
            return {'success': True, 'downloaded': downloaded_in_email}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _report_progress(self, current_email: int, total_emails: int):
        """Report download progress with ETA"""
        elapsed = time.time() - self.start_time
        
        if self.downloaded_count > 0:
            rate = self.downloaded_count / elapsed  # files per second
            eta_seconds = (10000 - self.downloaded_count) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            logger.info(f"Progress: {self.downloaded_count} files | "
                       f"Rate: {rate:.1f} files/sec | "
                       f"ETA: {eta_minutes:.0f} minutes | "
                       f"Size: {self.total_size / (1024*1024):.1f}MB")
    
    def _save_progress(self, progress_file: Path, completed_emails: set):
        """Save progress to file for resume capability"""
        try:
            progress_data = {
                'completed_emails': list(completed_emails),
                'timestamp': datetime.now().isoformat(),
                'downloaded_count': self.downloaded_count,
                'failed_count': self.failed_count
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")


# Performance estimation function
def estimate_download_time(num_emails: int, avg_attachments_per_email: int = 2, 
                         avg_file_size_mb: float = 1.5, concurrent_workers: int = 5) -> Dict:
    """Estimate download time for large datasets"""
    
    total_files = num_emails * avg_attachments_per_email
    total_size_gb = (total_files * avg_file_size_mb) / 1024
    
    # Timing estimates (seconds)
    api_call_time = 0.3  # per email
    download_time_per_mb = 0.5  # depends on connection
    
    # Sequential timing
    sequential_api_time = num_emails * api_call_time
    sequential_download_time = total_files * avg_file_size_mb * download_time_per_mb
    sequential_total_hours = (sequential_api_time + sequential_download_time) / 3600
    
    # Concurrent timing (with overhead)
    concurrent_efficiency = 0.7  # 70% efficiency due to overhead
    concurrent_total_hours = sequential_total_hours / (concurrent_workers * concurrent_efficiency)
    
    return {
        'total_files': total_files,
        'total_size_gb': round(total_size_gb, 2),
        'sequential_hours': round(sequential_total_hours, 2),
        'concurrent_hours': round(concurrent_total_hours, 2),
        'recommended_workers': min(concurrent_workers, 8),  # Don't overwhelm API
        'estimated_bandwidth_mbps': round((total_size_gb * 1024 * 8) / (concurrent_total_hours * 3600), 1)
    }


if __name__ == "__main__":
    # Example usage and estimation
    estimate = estimate_download_time(
        num_emails=5000,  # Emails with attachments
        avg_attachments_per_email=2,
        avg_file_size_mb=1.5,
        concurrent_workers=5
    )
    
    print("Performance Estimate for Large Download:")
    print(f"Total files: {estimate['total_files']:,}")
    print(f"Total size: {estimate['total_size_gb']} GB")
    print(f"Sequential time: {estimate['sequential_hours']:.1f} hours")
    print(f"Concurrent time: {estimate['concurrent_hours']:.1f} hours")
    print(f"Recommended workers: {estimate['recommended_workers']}")