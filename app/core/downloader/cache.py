"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.cache
- RESPONSIBILITY: Checks if the downloaded files already exist in the target directory.
- CALLED BY: app.core.downloader.manager
- CALLS TO: None
- IN = OUT: Returns True if all expected files exist, False otherwise.
=============================================================================
"""
import os
from .task import DownloadTask, TaskStatus

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
