"""
========================================================================
[AI_ARCH_NOTE]: HUGGINGFACE DOWNLOADER
- Purpose: Handles the actual downloading of models from HuggingFace via snapshot_download or hf_hub_download.
- Structure: Methods for downloading with progress tracking.
- Consumed by: manager.py
- Modified by: Developers
- Critical Rules: Must emit progress signals for the UI.
========================================================================
"""

class HFDownloader:
    def __init__(self):
        pass
        
    def download_model(self, repo_id, allow_patterns=None, ignore_patterns=None):
        """
        Downloads a model from HuggingFace.
        To be implemented: replace logic from TranslatorSoftwareUpdateWorker.
        """
        pass
