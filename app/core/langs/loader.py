"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.loader
- RESPONSIBILITY: Scans and loads .yaml localization files from .config/langs/.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Reads YAML files and returns Python dictionaries.
=============================================================================
"""

import os
from typing import Dict, Any

class LanguageLoader:
    def __init__(self, project_base_dir: str):
        self.langs_dir = os.path.join(project_base_dir, ".config", "langs")

    def load_localization_files(self) -> Dict[str, Any]:
        """Scans the langs directory and loads all .yaml or .yml files."""
        localization = {}
        if not os.path.exists(self.langs_dir):
            return localization

        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')
        
        try:
            for filename in os.listdir(self.langs_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    file_path = os.path.join(self.langs_dir, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.load(f) or {}
                    
                    lang_id = data.get("id")
                    if not lang_id:
                        lang_id = os.path.splitext(filename)[0]
                        print(f"[LanguageLoader] Warning: {filename} missing 'id' field. Falling back to filename '{lang_id}'.")
                        
                    localization[lang_id] = data
        except Exception as e:
            print(f"[LanguageLoader] Error loading files in langs directory: {e}")
            
        return localization
