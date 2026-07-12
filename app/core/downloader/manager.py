"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.manager
- RESPONSIBILITY: Central manager for all downloading, caching, verifying, and extracting tasks.
- CALLED BY: Various models and services requiring external assets.
- CALLS TO: app.core.downloader.utils
- IN = OUT: Executes DownloadTask -> returns True/False.
=============================================================================
"""
import os
import urllib.request
from typing import Callable, Optional
from .models import DownloadTask, TaskStatus
from .utils import CacheChecker, ChecksumVerifier, FileExtractor

class DownloadManager:
    """Quản lý và thực thi các tác vụ tải xuống theo trình tự: cache -> download -> verify -> extract."""

    def __init__(self):
        self.cache_checker = CacheChecker()
        self.checksum_verifier = ChecksumVerifier()
        self.extractor = FileExtractor()

    def execute(self, task: DownloadTask, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Thực thi toàn bộ luồng tải xuống."""
        if self.cache_checker.check(task, log_callback):
            return True

        os.makedirs(task.target_dir, exist_ok=True)
        download_path = os.path.join(task.target_dir, task.filename)

        try:
            self._download(task, download_path, log_callback)
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

    def _download(self, task: DownloadTask, download_path: str, log_callback=None):
        """Tải file từ URL về thư mục đích."""
        task.status = TaskStatus.DOWNLOADING
        msg = f"Bắt đầu tải mô hình từ: {task.url}"
        if log_callback: log_callback("INFO", msg)
        else: print(f"[LOG:INFO] {msg}")

        def _reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = min(int(count * block_size * 100 / total_size), 100)
                task.progress = percent
                if count % max(1, (total_size // block_size // 10)) == 0:
                    prog_msg = f"Đang tải {task.filename}... {percent}%"
                    if log_callback: log_callback("INFO", prog_msg)
                    else: print(f"[LOG:INFO] {prog_msg}")

        urllib.request.urlretrieve(task.url, download_path, reporthook=_reporthook)

        done_msg = f"Tải hoàn tất: {task.filename}"
        if log_callback: log_callback("INFO", done_msg)
        else: print(f"[LOG:INFO] {done_msg}")
