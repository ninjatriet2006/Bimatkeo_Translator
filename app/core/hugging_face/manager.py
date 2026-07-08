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
from .verify import HFVerifier

class HuggingFaceManager:
    def __init__(self):
        self.downloader = HFDownloader()
        self.version_checker = HFVersionChecker()
        self.verifier = HFVerifier()
        
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
        import os
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        
        local_versions = {}
        if os.path.exists(local_versions_file):
            with open(local_versions_file, "r", encoding="utf-8") as lf:
                local_versions = yaml.load(lf) or {}
                
        if key not in local_versions:
            local_versions[key] = {}
            
        local_versions[key][model_name] = version
        
        with open(local_versions_file, "w", encoding="utf-8") as lf:
            yaml.dump(local_versions, lf)
