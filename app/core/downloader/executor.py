"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.executor
- RESPONSIBILITY: Executes the sequential download pipeline (cache -> download -> verify -> extract).
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.cache, app.core.downloader.download, app.core.downloader.checksum, app.core.downloader.extract
- IN = OUT: Receives DownloadTask, orchestrates the steps, handles errors, returns True/False.
=============================================================================
"""
import os
from typing import Callable, Optional
from .task import DownloadTask, TaskStatus
from .cache import CacheChecker
from .download import FileDownloader
from .checksum import ChecksumVerifier
from .extract import FileExtractor

class DownloadExecutor:
    """Chịu trách nhiệm thực thi trình tự các bước tải xuống."""
    
    def __init__(self):
        self.cache_checker = CacheChecker()
        self.downloader = FileDownloader()
        self.checksum_verifier = ChecksumVerifier()
        self.extractor = FileExtractor()
        
    def execute(self, task: DownloadTask, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        if self.cache_checker.check(task, log_callback):
            return True
            
        os.makedirs(task.target_dir, exist_ok=True)
        download_path = os.path.join(task.target_dir, task.filename)
        
        try:
            self.downloader.download(task, download_path, log_callback)
            self.checksum_verifier.check(task, download_path, log_callback)
            self.extractor.extract(task, download_path, log_callback)
            
            task.status = TaskStatus.COMPLETED
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            
            msg = f"Lỗi trong quá trình tải/giải nén: {e}"
            if log_callback:
                log_callback("ERROR", msg)
            else:
                print(f"[LOG:ERROR] {msg}")
            
            if os.path.exists(download_path):
                os.remove(download_path)
            return False
