"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader
- RESPONSIBILITY: Expose downloader components and backward-compatible ModelDownloader.
- CALLED BY: app.core.shared_registry, app.core.fonts.manager, app.core.hugging_face.downloader, app.core.inpainter.manager, desktop_ui.main_window.handlers
- CALLS TO: app.core.downloader.task, app.core.downloader.manager, app.core.downloader.exceptions
- IN = OUT: Initialization module.
=============================================================================
"""
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
        manager = DownloadManager()
        return manager.execute(task, log_callback=log_callback)

__all__ = [
    'ModelDownloader',
    'DownloadTask',
    'DownloadManager',
    'TaskStatus',
    'DownloadError',
    'ChecksumMismatchError',
    'ExtractionError'
]
