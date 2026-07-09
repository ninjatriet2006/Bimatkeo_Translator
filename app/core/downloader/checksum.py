"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.checksum
- RESPONSIBILITY: Computes SHA256 checksum and compares with expected hash.
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.exceptions
- IN = OUT: Raises ChecksumMismatchError if invalid, returns True if valid.
=============================================================================
"""
import hashlib
from .exceptions import ChecksumMismatchError

class ChecksumVerifier:
    """Xác thực mã băm SHA256 của file tải về."""
    
    def check(self, file_path: str, expected_checksum: str) -> bool:
        """
        Nếu sai lệch, ném ra ngoại lệ ChecksumMismatchError.
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
                
        if hasher.hexdigest() != expected_checksum:
            raise ChecksumMismatchError("Sai lệch mã băm (Checksum Mismatch). File có thể bị hỏng!")
        
        return True
