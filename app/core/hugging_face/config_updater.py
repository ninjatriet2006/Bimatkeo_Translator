"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.config_updater
- RESPONSIBILITY: Handle YAML read/write operations for hugging face config.
- CALLED BY: app.core.hugging_face.manager
- CALLS TO: None
- IN = OUT: Receives paths and data -> updates YAML files.
=============================================================================
"""
import os
from ruamel.yaml import YAML

class HFConfigUpdater:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    def update_local_version(self, local_versions_file: str, key: str, model_name: str, version: str):
        """Records the downloaded version in local_versions.yaml."""
        local_versions = {}
        if os.path.exists(local_versions_file):
            with open(local_versions_file, "r", encoding="utf-8") as lf:
                local_versions = self.yaml.load(lf) or {}
                
        if key not in local_versions:
            local_versions[key] = {}
            
        local_versions[key][model_name] = version
        
        with open(local_versions_file, "w", encoding="utf-8") as lf:
            self.yaml.dump(local_versions, lf)
