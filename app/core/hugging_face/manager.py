"""
========================================================================
[AI_ARCH_NOTE]: HUGGINGFACE MANAGER
- Purpose: Orchestrates version checking and downloading for HuggingFace models.
- Structure: High-level methods connecting VersionChecker and Downloader.
- Consumed by: UI update workers (handlers.py).
- Modified by: Developers
- Critical Rules: None.
========================================================================
"""

from .downloader import HFDownloader
from .version_checker import HFVersionChecker

class HuggingFaceManager:
    def __init__(self):
        self.downloader = HFDownloader()
        self.version_checker = HFVersionChecker()
        
    def check_and_update(self, repo_id: str, local_version: str):
        """
        Checks for update and downloads if a new version is available.
        To be implemented.
        """
        pass
