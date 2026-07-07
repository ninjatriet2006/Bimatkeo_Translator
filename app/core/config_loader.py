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
        
        self._migrate_local_versions()

    def _migrate_local_versions(self):
        local_versions_path = os.path.join(self.project_base_dir, ".config", "models", "local_versions.yaml")
        if not os.path.exists(local_versions_path):
            return
            
        local_versions = self._load_yaml_file(local_versions_path)
        if not local_versions:
            return
            
        # Check if it's already nested (if any value is a dictionary, it's considered migrated)
        is_flat = any(isinstance(v, str) for v in local_versions.values())
        if not is_flat:
            return
            
        print("[ConfigLoader] Migrating local_versions.yaml to nested structure...")
        registry_path = os.path.join(self.project_base_dir, ".config", "models", "model_registry.yaml")
        registry = self._load_yaml_file(registry_path)
        
        # Build a map from model_key -> category
        model_to_category = {}
        fields = registry.get("fields", {})
        for tab, categories in fields.items():
            if isinstance(categories, dict):
                for category, models in categories.items():
                    if isinstance(models, list):
                        for model in models:
                            model_to_category[model.get("key")] = category
                            
        new_versions = {}
        for k, v in local_versions.items():
            if isinstance(v, dict):
                new_versions[k] = v
                continue
                
            cat = model_to_category.get(k, "uncategorized")
            if cat not in new_versions:
                new_versions[cat] = {}
            new_versions[cat][k] = v
            
        # Also migrate fonts from oldsession if present
        oldsession_path = os.path.join(self.project_base_dir, ".config", "configs", "oldsession.yaml")
        if os.path.exists(oldsession_path):
            oldsession = self._load_yaml_file(oldsession_path)
            if "font_versions" in oldsession:
                new_versions["fonts"] = oldsession.pop("font_versions")
                self._save_yaml_file(oldsession_path, oldsession)
                print("[ConfigLoader] Migrated font_versions from oldsession.yaml")
                
        # Preserve header note by writing it out if missing? The _save_yaml_file will overwrite,
        # but that's acceptable for an automated migration (it's a one-time thing for old users).
        self._save_yaml_file(local_versions_path, new_versions)
        print("[ConfigLoader] Migration of local_versions.yaml complete.")


