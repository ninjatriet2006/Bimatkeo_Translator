"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.manager
- RESPONSIBILITY: Facade pattern delegator for download tasks.
- CALLED BY: app.core.downloader
- CALLS TO: app.core.downloader.executor
- IN = OUT: Receives DownloadTask -> delegates to DownloadExecutor -> returns True/False.
=============================================================================
"""
from typing import Callable, Optional
from .task import DownloadTask
from .executor import DownloadExecutor

class DownloadManager:
    """Quản lý và thực thi các tác vụ tải xuống theo chuẩn Facade ngắn gọn."""
    
    def __init__(self):
        self.executor = DownloadExecutor()
        
    def execute(self, task: DownloadTask, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Facade method: uỷ quyền thực thi toàn bộ luồng cho executor."""
        return self.executor.execute(task, log_callback)
