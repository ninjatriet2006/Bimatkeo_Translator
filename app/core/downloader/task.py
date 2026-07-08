from enum import Enum
from typing import List, Optional

class TaskStatus(Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    VERIFYING = "VERIFYING"
    EXTRACTING = "EXTRACTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class DownloadTask:
    """Mô tả một tác vụ tải xuống."""
    def __init__(self, url: str, target_dir: str, expected_files: List[str] = None, 
                 extract: bool = False, checksum: Optional[str] = None):
        self.url = url
        self.target_dir = target_dir
        self.expected_files = expected_files or []
        self.extract = extract
        self.checksum = checksum
        
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.error_message = ""
        
        # Tự động trích xuất tên file từ URL
        filename = self.url.split('/')[-1]
        if "?" in filename:
            filename = filename.split("?")[0]
        self.filename = filename
