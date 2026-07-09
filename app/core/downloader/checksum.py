"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.checksum
- RESPONSIBILITY: Computes SHA256 checksum and compares with expected hash.
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.exceptions
- IN = OUT: Raises ChecksumMismatchError if invalid, returns True if valid.
=============================================================================
"""
import os
import hashlib
from .task import DownloadTask, TaskStatus
from .exceptions import ChecksumMismatchError

class ChecksumVerifier:
    """Xác thực mã băm SHA256 của file tải về."""
    
    def check(self, task: DownloadTask, download_path: str, log_callback=None) -> bool:
        if not task.checksum:
            return True
            
        task.status = TaskStatus.VERIFYING
        msg = "Đang xác thực mã băm SHA256..."
        if log_callback: log_callback("INFO", msg)
        else: print(f"[LOG:INFO] {msg}")
        
        hasher = hashlib.sha256()
        with open(download_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
                
        if hasher.hexdigest() != task.checksum:
            if os.path.exists(download_path):
                os.remove(download_path)
            raise ChecksumMismatchError("Sai lệch mã băm (Checksum Mismatch). File có thể bị hỏng!")
            
        ok_msg = "Xác thực mã băm thành công."
        if log_callback: log_callback("INFO", ok_msg)
        else: print(f"[LOG:INFO] {ok_msg}")
        return True
