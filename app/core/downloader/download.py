"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.download
- RESPONSIBILITY: Handles retrieving files from a URL using urllib.
- CALLED BY: app.core.downloader.manager
- CALLS TO: None
- IN = OUT: Downloads file to disk and reports progress.
=============================================================================
"""
import urllib.request
from .task import DownloadTask, TaskStatus

class FileDownloader:
    """Tải file từ URL về thư mục đích."""
    
    def download(self, task: DownloadTask, download_path: str, log_callback=None):
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
