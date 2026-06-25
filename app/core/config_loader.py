import os
import json
import subprocess
import sys
import re

from .utils import get_python_executable
from .base_config import BaseConfigLoader

class ConfigLoader(BaseConfigLoader):
    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = get_python_executable(self.project_base_dir)
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        self.studio_config_path = os.path.join(self.project_base_dir, ".config", "configs", "studio_config.yaml")

        self.studio_config = self._load_yaml_file(self.studio_config_path)

        self.backend_schema = self._load_backend_schema()
        self.ui_map = self._load_ui_map()


        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()


