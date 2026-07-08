"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.manager
- RESPONSIBILITY: Quản lý và thực thi các tác vụ tải xuống (download, verify, extract).
- CALLED BY: app.core.downloader
- CALLS TO: app.core.downloader.task, app.core.downloader.exceptions
- IN = OUT: Nhận DownloadTask -> tải và giải nén -> trả về True/False.
=============================================================================
"""
import os
import urllib.request
import zipfile
import tarfile
import hashlib
from typing import Callable, Optional

from .task import DownloadTask, TaskStatus
from .exceptions import DownloadError, ChecksumMismatchError, ExtractionError

class DownloadManager:
    """Quản lý và thực thi các tác vụ tải xuống."""
    
    @staticmethod
    def execute(task: DownloadTask, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Thực thi một tác vụ tải. Trả về True nếu thành công hoặc bỏ qua."""
        
        def _log(level: str, msg: str):
            if log_callback:
                log_callback(level, msg)
            else:
                print(f"[LOG:{level}] {msg}")

        # Kiểm tra nếu file đã tồn tại
        if task.expected_files and all(os.path.exists(os.path.join(task.target_dir, f)) for f in task.expected_files):
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
            urllib.request.urlretrieve(task.url, download_path, reporthook=_reporthook)
            _log("INFO", f"Tải hoàn tất: {task.filename}")
            
            # Verify Checksum
            if task.checksum:
                task.status = TaskStatus.VERIFYING
                _log("INFO", "Đang xác thực mã băm SHA256...")
                hasher = hashlib.sha256()
                with open(download_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                if hasher.hexdigest() != task.checksum:
                    os.remove(download_path)
                    raise ChecksumMismatchError("Sai lệch mã băm (Checksum Mismatch). File có thể bị hỏng!")
                _log("INFO", "Xác thực mã băm thành công.")
            
            # Extract
            if task.extract:
                task.status = TaskStatus.EXTRACTING
                if download_path.endswith('.zip'):
                    _log("INFO", "Đang giải nén tệp tin zip...")
                    try:
                        with zipfile.ZipFile(download_path, 'r') as zip_ref:
                            zip_ref.extractall(task.target_dir)
                    except Exception as e:
                        raise ExtractionError(f"Lỗi giải nén file zip: {e}")
                    finally:
                        os.remove(download_path)
                    _log("INFO", "Giải nén hoàn tất.")
                    
                elif download_path.endswith('.tar') or download_path.endswith('.tar.gz'):
                    _log("INFO", "Đang giải nén tệp tin tar...")
                    try:
                        with tarfile.open(download_path, 'r:*') as tar_ref:
                            tar_ref.extractall(task.target_dir)
                    except Exception as e:
                        raise ExtractionError(f"Lỗi giải nén file tar: {e}")
                    finally:
                        os.remove(download_path)
                    _log("INFO", "Giải nén hoàn tất.")
            
            task.status = TaskStatus.COMPLETED
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _log("ERROR", f"Lỗi trong quá trình tải/giải nén: {e}")
            if os.path.exists(download_path):
                os.remove(download_path)
            return False
