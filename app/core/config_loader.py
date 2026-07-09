"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.config_loader
- RESPONSIBILITY: Central application configuration management.
- CALLED BY: main.py
- CALLS TO: app.core.base.base_loader
- IN = OUT: Main entry point for loading settings, delegating to base config.
=============================================================================
"""
import os
import json
import subprocess
import sys
import re

from .utils import get_python_executable
from .base import BaseConfigLoader

class ConfigLoader(BaseConfigLoader):
    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = get_python_executable(self.project_base_dir)
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        self.backend_schema = self._load_backend_schema()


        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
