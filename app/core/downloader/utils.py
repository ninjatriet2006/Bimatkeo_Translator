"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.utils
- RESPONSIBILITY: Contains utilities for caching, checksum validation, and extraction.
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.models
- IN = OUT: Helper methods for downloader.
=============================================================================
"""
import os
import hashlib
import zipfile
import tarfile
from .models import DownloadTask, TaskStatus, ChecksumMismatchError, ExtractionError

class CacheChecker:
    """Kiểm tra xem các file yêu cầu đã tồn tại đầy đủ trong thư mục chưa."""

    def check(self, task: DownloadTask, log_callback=None) -> bool:
        if task.expected_files and all(os.path.exists(os.path.join(task.target_dir, f)) for f in task.expected_files):
            task.status = TaskStatus.SKIPPED
            task.progress = 100
            msg = f"Mô hình đã tồn tại đầy đủ tại {task.target_dir}. Bỏ qua tải."
            if log_callback:
                log_callback("INFO", msg)
            else:
                print(f"[LOG:INFO] {msg}")
            return True
        return False

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
