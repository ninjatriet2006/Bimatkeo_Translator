"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.downloader.extract
- RESPONSIBILITY: Extracts downloaded zip or tar files.
- CALLED BY: app.core.downloader.manager
- CALLS TO: app.core.downloader.exceptions
- IN = OUT: Extracts files to target directory, raises ExtractionError on fail.
=============================================================================
"""
import zipfile
import tarfile
from .exceptions import ExtractionError

class FileExtractor:
    """Giải nén file (.zip, .tar, .tar.gz) vào thư mục đích."""
    
    def extract(self, download_path: str, target_dir: str):
        if download_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            except Exception as e:
                raise ExtractionError(f"Lỗi giải nén file zip: {e}")
                
        elif download_path.endswith('.tar') or download_path.endswith('.tar.gz'):
            try:
                with tarfile.open(download_path, 'r:*') as tar_ref:
                    tar_ref.extractall(target_dir)
            except Exception as e:
                raise ExtractionError(f"Lỗi giải nén file tar: {e}")
