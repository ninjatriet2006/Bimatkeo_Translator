"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.manager
- RESPONSIBILITY: Central orchestrator for HuggingFace models.
- CALLED BY: desktop_ui.mainwindow.handlers
- CALLS TO: app.core.hugging_face.version_checker, app.core.hugging_face.downloader
- IN = OUT: Orchestrates VersionChecker and Downloader.
========================================================================
"""

from .downloader import HFDownloader
from .version_checker import HFVersionChecker
from .verify import HFVerifier
from .config_updater import HFConfigUpdater

class HuggingFaceManager:
    def __init__(self):
        self.downloader = HFDownloader()
        self.version_checker = HFVersionChecker()
        self.verifier = HFVerifier()
        self.config_updater = HFConfigUpdater()
        
    def run_verification(self, registry_path: str, local_versions_path: str):
        """Runs integrity check on the HuggingFace module configs."""
        self.verifier.run_verification(registry_path, local_versions_path)
        
    def check_version(self, repo_id: str) -> str:
        """
        Returns the latest formatted version string.
        """
        return self.version_checker.get_latest_version(repo_id)
        
    def download(self, repo_id: str, model_dir: str, hf_specific_file: str | None = None, progress_callback=None):
        """
        Downloads a standard model.
        """
        self.downloader.download_model(repo_id, model_dir, hf_specific_file, progress_callback)

    def download_diffusers(self, repo_id: str, progress_callback=None):
        """
        Downloads a diffusers pipeline model using huggingface_hub.
        """
        self.downloader.download_diffusers(repo_id, progress_callback)

    def update_local_version(self, local_versions_file: str, key: str, model_name: str, version: str):
        """
        Records the downloaded version in local_versions.yaml.
        """
        self.config_updater.update_local_version(local_versions_file, key, model_name, version)
