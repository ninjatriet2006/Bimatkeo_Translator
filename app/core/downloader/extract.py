"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.extract
- RESPONSIBILITY: Extracts downloaded zip or tar files.
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.exceptions
- IN = OUT: Extracts files to target directory, raises ExtractionError on fail.
=============================================================================
"""
import os
import zipfile
import tarfile
from .task import DownloadTask, TaskStatus
from .exceptions import ExtractionError

class FileExtractor:
    """Giải nén file (.zip, .tar, .tar.gz) vào thư mục đích."""
    
    def extract(self, task: DownloadTask, download_path: str, log_callback=None):
        if not task.extract:
            return
            
        task.status = TaskStatus.EXTRACTING
        msg = f"Đang giải nén tệp tin {task.filename}..."
        if log_callback: log_callback("INFO", msg)
        else: print(f"[LOG:INFO] {msg}")
        
        try:
            if download_path.endswith('.zip'):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(task.target_dir)
            elif download_path.endswith('.tar') or download_path.endswith('.tar.gz'):
                with tarfile.open(download_path, 'r:*') as tar_ref:
                    tar_ref.extractall(task.target_dir)
                    
            done_msg = "Giải nén hoàn tất."
            if log_callback: log_callback("INFO", done_msg)
            else: print(f"[LOG:INFO] {done_msg}")
        except Exception as e:
            raise ExtractionError(f"Lỗi giải nén file zip/tar: {e}")
        finally:
            if os.path.exists(download_path):
                os.remove(download_path)
