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
        
    def check_version(self, repo_id: str) -> str:
        """
        Returns the latest formatted version string.
        """
        return self.version_checker.get_latest_version(repo_id)
        
    def download(self, repo_id: str, model_dir: str, hf_specific_file: str = None, progress_callback=None):
        """
        Downloads a standard model.
        """
        self.downloader.download_model(repo_id, model_dir, hf_specific_file, progress_callback)

    def download_diffusers(self, repo_id: str, progress_callback=None):
        """
        Downloads a diffusers pipeline model using huggingface_hub.
        """
        self.downloader.download_diffusers(repo_id, progress_callback)
