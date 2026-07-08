"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.exceptions
- RESPONSIBILITY: Định nghĩa các lỗi (exceptions) đặc thù cho việc tải xuống.
- CALLED BY: app.core.downloader, app.core.downloader.manager
- CALLS TO: None
- IN = OUT: Custom exception classes.
=============================================================================
"""
class DownloadError(Exception):
    """Lỗi chung trong quá trình tải xuống."""
    pass

class ChecksumMismatchError(DownloadError):
    """Lỗi khi mã băm (checksum) không khớp với giá trị mong đợi."""
    pass

class ExtractionError(DownloadError):
    """Lỗi trong quá trình giải nén tệp tin."""
    pass
