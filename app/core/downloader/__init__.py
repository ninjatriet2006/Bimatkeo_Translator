from typing import Optional, Callable

from .task import DownloadTask, TaskStatus
from .manager import DownloadManager
from .exceptions import DownloadError, ChecksumMismatchError, ExtractionError

class ModelDownloader:
    """
    Adapter tương thích ngược (Backward Compatibility).
    Đảm bảo các module/plugins hiện tại sử dụng `ModelDownloader.download_and_extract`
    vẫn hoạt động bình thường mà không cần sửa code.
    """
    
    @staticmethod
    def download_and_extract(url: str, target_dir: str, expected_files: list[str], 
                             log_callback: Optional[Callable] = None, 
                             extract: bool = False, checksum: Optional[str] = None) -> bool:
        
        task = DownloadTask(
            url=url, 
            target_dir=target_dir, 
            expected_files=expected_files, 
            extract=extract, 
            checksum=checksum
        )
        return DownloadManager.execute(task, log_callback=log_callback)

__all__ = [
    'ModelDownloader',
    'DownloadTask',
    'DownloadManager',
    'TaskStatus',
    'DownloadError',
    'ChecksumMismatchError',
    'ExtractionError'
]
