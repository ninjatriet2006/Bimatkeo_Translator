"""
========================================================================
[AI_ARCH_NOTE]: HUGGINGFACE MODULE INIT
- Purpose: Public API for the hugging_face module.
- Structure: Exposes main functions from the manager, downloader, and version_checker.
- Consumed by: app/core/pipeline.py, desktop_ui/mainwindow/handlers.py
- Modified by: Developers
- Critical Rules: Keep exports minimal. Do not expose internal implementation details.
========================================================================
"""
from .manager import HuggingFaceManager
from .downloader import HFDownloader
from .version_checker import HFVersionChecker

__all__ = ["HuggingFaceManager", "HFDownloader", "HFVersionChecker"]
