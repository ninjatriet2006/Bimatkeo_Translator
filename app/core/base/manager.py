"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.manager
- RESPONSIBILITY: Central application configuration management for the core.
- CALLED BY: main.py, app.core.verify_utils, app.core.desktop.config
- CALLS TO: app.core.base.base_loader
- IN = OUT: Main entry point for loading settings, delegating to base config.
=============================================================================
"""
import os
import json
import subprocess
import sys
import re

from app.core.base.env import get_python_executable
from app.core.base.base_loader import BaseConfigLoader

class ConfigManager(BaseConfigLoader):
    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = get_python_executable(self.project_base_dir)
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        self.backend_schema = self._load_backend_schema()

        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()

    def verify(self) -> tuple[bool, str]:
        """
        Kiểm tra tính toàn vẹn của phân hệ config/base.
        Trả về True nếu schema và factory_defaults được load thành công.
        """
        if not self.backend_schema:
            return False, "Base configuration verification failed: backend_schema is empty or None."
        
        if not hasattr(self, 'factory_defaults') or not self.factory_defaults:
            return False, "Base configuration verification failed: factory_defaults is empty."
            
        return True, "Base configuration verification successful."
