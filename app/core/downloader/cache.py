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

class CacheChecker:
    """Kiểm tra xem các file yêu cầu đã tồn tại đầy đủ trong thư mục chưa."""
    
    def check(self, expected_files: list, target_dir: str) -> bool:
        if expected_files and all(os.path.exists(os.path.join(target_dir, f)) for f in expected_files):
            return True
        return False
