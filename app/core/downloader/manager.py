"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.manager
- RESPONSIBILITY: Manages and executes download tasks (download, verify, extract).
- CALLED BY: app.core.downloader
- CALLS TO: app.core.downloader.task, app.core.downloader.exceptions, app.core.downloader.cache, app.core.downloader.download, app.core.downloader.checksum, app.core.downloader.extract
- IN = OUT: Receives DownloadTask -> downloads and extracts -> returns True/False.
=============================================================================
"""
import os
from typing import Callable, Optional

from .task import DownloadTask, TaskStatus
from .exceptions import DownloadError, ChecksumMismatchError
from .cache import CacheChecker
from .download import FileDownloader
from .checksum import ChecksumVerifier
from .extract import FileExtractor

class DownloadManager:
    """Quản lý và thực thi các tác vụ tải xuống."""
    
    def __init__(self):
        self.cache_checker = CacheChecker()
        self.downloader = FileDownloader()
        self.checksum_verifier = ChecksumVerifier()
        self.extractor = FileExtractor()
        
    def execute(self, task: DownloadTask, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Thực thi một tác vụ tải. Trả về True nếu thành công hoặc bỏ qua."""
        
        def _log(level: str, msg: str):
            if log_callback:
                log_callback(level, msg)
            else:
                print(f"[LOG:{level}] {msg}")

        # Kiểm tra nếu file đã tồn tại
        if self.cache_checker.check(task.expected_files, task.target_dir):
            task.status = TaskStatus.SKIPPED
            task.progress = 100
            _log("INFO", f"Mô hình đã tồn tại đầy đủ tại {task.target_dir}. Bỏ qua tải.")
            return True
            
        os.makedirs(task.target_dir, exist_ok=True)
        download_path = os.path.join(task.target_dir, task.filename)
        
        def _reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                if percent > 100: percent = 100
                task.progress = percent
                
                # Tránh in log quá nhiều lần
                if count % max(1, (total_size // block_size // 10)) == 0:
                    _log("INFO", f"Đang tải {task.filename}... {percent}%")

        try:
            task.status = TaskStatus.DOWNLOADING
            _log("INFO", f"Bắt đầu tải mô hình từ: {task.url}")
            
            self.downloader.download(task.url, download_path, progress_callback=_reporthook)
            _log("INFO", f"Tải hoàn tất: {task.filename}")
            
            # Verify Checksum
            if task.checksum:
                task.status = TaskStatus.VERIFYING
                _log("INFO", "Đang xác thực mã băm SHA256...")
                try:
                    self.checksum_verifier.check(download_path, task.checksum)
                    _log("INFO", "Xác thực mã băm thành công.")
                except ChecksumMismatchError as e:
                    os.remove(download_path)
                    raise e
            
            # Extract
            if task.extract:
                task.status = TaskStatus.EXTRACTING
                _log("INFO", f"Đang giải nén tệp tin {task.filename}...")
                try:
                    self.extractor.extract(download_path, task.target_dir)
                    _log("INFO", "Giải nén hoàn tất.")
                finally:
                    os.remove(download_path)
            
            task.status = TaskStatus.COMPLETED
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _log("ERROR", f"Lỗi trong quá trình tải/giải nén: {e}")
            if os.path.exists(download_path):
                os.remove(download_path)
            return False
