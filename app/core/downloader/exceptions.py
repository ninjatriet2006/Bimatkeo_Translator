class DownloadError(Exception):
    """Lỗi chung trong quá trình tải xuống."""
    pass

class ChecksumMismatchError(DownloadError):
    """Lỗi khi mã băm (checksum) không khớp với giá trị mong đợi."""
    pass

class ExtractionError(DownloadError):
    """Lỗi trong quá trình giải nén tệp tin."""
    pass
