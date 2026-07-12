"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.__init__
- RESPONSIBILITY: Entrypoint for downloader module.
- CALLED BY: external components needing download capability.
=============================================================================
"""
from .manager import DownloadManager
from .models import DownloadTask, TaskStatus, DownloadError, ChecksumMismatchError, ExtractionError
from typing import Optional, Callable

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
    "DownloadManager",
    "ModelDownloader",
    "DownloadTask",
    "TaskStatus",
    "DownloadError",
    "ChecksumMismatchError",
    "ExtractionError"
]
