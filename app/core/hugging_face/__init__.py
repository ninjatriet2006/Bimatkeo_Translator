"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.__init__
- RESPONSIBILITY: Public API for the hugging_face module.
- CALLED BY: app.core.pipeline.manager, desktop_ui.mainwindow.handlers
- CALLS TO: app.core.hugging_face.manager, app.core.hugging_face.downloader, app.core.hugging_face.version_checker
- IN = OUT: Exposes main functions. Keep exports minimal. Do not expose internal implementation details.
========================================================================
"""
from .manager import HuggingFaceManager
from .downloader import HFDownloader
from .version_checker import HFVersionChecker

__all__ = ["HuggingFaceManager", "HFDownloader", "HFVersionChecker"]
