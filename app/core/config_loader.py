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

        import yaml  # type: ignore
        self.studio_config = {}
        if os.path.exists(self.studio_config_path):
            try:
                with open(self.studio_config_path, "r", encoding="utf-8") as f:
                    self.studio_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading studio_config.yaml: {e}")

        self.backend_schema = self._load_backend_schema()
        self.ui_map = self._load_ui_map()
        self.tasks_config = self._load_tasks_config()

        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
        self.full_config_data = self._build_full_config_data()

    def _build_full_config_data(self):
        """Builds the final, merged config data for the UI, reading ALL properties."""
        if not self.ui_map:
            return {}
        full_data = {}
        all_properties = {}

        # 1. Gather all root-level properties
        root_props = self.backend_schema.get("properties", {}) if self.backend_schema else {}
        all_properties.update(root_props)

        # 2. Gather all nested properties from complex types (e.g., DetectorConfig)
        for prop in root_props.values():
            ref_path = prop.get("allOf", [{}])[0].get('$ref')
            if ref_path:
                config_def = self._get_definition_from_ref(ref_path)
                if config_def and "properties" in config_def:
                    all_properties.update(config_def["properties"])

        # 3. Build the final data structure using the UI map as the guide
        for key, ui_info in self.ui_map.items():
            if key.startswith("__"):
                continue
            merged_info = ui_info.copy()
            merged_info['key'] = key

            merged_info['default'] = self.factory_defaults.get(key)

            # Add enum values (for dropdowns) if they exist
            prop_def = all_properties.get(key)
            if prop_def and isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)
                    if enum_def and "enum" in enum_def:
                        merged_info['values'] = enum_def["enum"]
            full_data[key] = merged_info
        return full_data
