"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.__init__
- RESPONSIBILITY: Exposes public interfaces for the pipeline package.
- CALLED BY: main.py
- CALLS TO: None
- IN = OUT: Package marker and export registry.
=============================================================================
"""
from app.core.pipeline.manager import PipelineManager
from app.core.pipeline.executor import PipelineExecutor

__all__ = ["PipelineManager", "PipelineExecutor"]
