"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.download
- RESPONSIBILITY: Handles retrieving files from a URL using urllib.
- CALLED BY: app.core.downloader.manager
- CALLS TO: None
- IN = OUT: Downloads file to disk and reports progress.
=============================================================================
"""
import urllib.request

class FileDownloader:
    """Tải file từ URL về thư mục đích."""
    
    def download(self, url: str, download_path: str, progress_callback=None):
        """
        progress_callback(count, block_size, total_size) dùng để báo cáo tiến độ.
        """
        urllib.request.urlretrieve(url, download_path, reporthook=progress_callback)
