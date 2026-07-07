# type: ignore
import os
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
from desktop_ui.constants import *


from typing import Dict, Any

class RepairMixin:
    project_base_dir: str
    _DEFAULT_CHECKS: dict
    def _get_flat_properties(self) -> Dict[str, Any]: return {}
    def _get_definition_from_ref(self, arg) -> Dict[str, Any]: return {}


    def _initialize_and_repair_config(self):
        """
        Ensures that .config/ exists and contains validated, repaired YAML files
        for languages (supporttargetlang.yaml) and all backend enum models (model_ocr.yaml, etc.).
        """
        config_dir = os.path.join(self.project_base_dir, ".config")
        os.makedirs(os.path.join(config_dir, "configs"), exist_ok=True)
        os.makedirs(os.path.join(config_dir, "models"), exist_ok=True)

        # 1. Repair supporttargetlang.yaml
        lang_yaml_path = os.path.join(config_dir, "configs", "supporttargetlang.yaml")
        old_lang_path = os.path.join(config_dir, "configs", "lang.yaml")
        
        if hasattr(self, 'languages') and self.languages:
            default_langs = {str(v): str(k) for k, v in self.languages.items()}
        else:
            default_langs = {
                "auto": "Auto-Detect", "ENG": "English", "TRK": "Turkish", "JPN": "Japanese",
                "KOR": "Korean", "CHS": "Simplified Chinese", "CHT": "Traditional Chinese",
                "ESP": "Spanish", "FRA": "French", "DEU": "German", "RUS": "Russian",
                "PTB": "Portuguese (Brazilian)", "ITA": "Italian", "POL": "Polish",
                "NLD": "Dutch", "CSY": "Czech", "HUN": "Hungarian", "ROM": "Romanian",
                "UKR": "Ukrainian", "VIN": "Vietnamese", "ARA": "Arabic", "SRP": "Serbian",
                "HRV": "Croatian", "THA": "Thai", "IND": "Indonesian", "FIL": "Filipino (Tagalog)"
            }

        loaded_langs = {}
        read_path = lang_yaml_path if os.path.exists(lang_yaml_path) else old_lang_path
        if os.path.exists(read_path):
            try:
                with open(read_path, 'r', encoding='utf-8') as f:
                    content = yaml.load(f)
                if isinstance(content, dict):
                    for k, v in content.items():
                        if k and v and isinstance(k, (str, int, float)) and isinstance(v, (str, int, float)):
                            loaded_langs[str(k)] = str(v)
            except Exception as e:
                print(f"[ConfigLoader] Error reading lang config: {e}")

        repaired_langs = default_langs.copy()
        repaired_langs.update(loaded_langs)

        try:
            with open(lang_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(repaired_langs, f)
            if os.path.exists(old_lang_path) and lang_yaml_path != old_lang_path:
                os.remove(old_lang_path)
        except Exception as e:
            print(f"[ConfigLoader] Error writing supporttargetlang.yaml: {e}")

    def _migrate_legacy_file_structures(self):
        """
        Migrates and copies default configurations, ensuring old root files are placed correctly.
        """
        config_dir = os.path.join(self.project_base_dir, ".config")
        default_configs_dir = os.path.join(self.project_base_dir, "default_configs")
        
        if os.path.exists(default_configs_dir):
            import shutil
            for root, _, files in os.walk(default_configs_dir):
                rel_path = os.path.relpath(root, default_configs_dir)
                dest_dir = os.path.join(config_dir, rel_path) if rel_path != "." else config_dir
                os.makedirs(dest_dir, exist_ok=True)
                for f in files:
                    src_f = os.path.join(root, f)
                    dst_f = os.path.join(dest_dir, f)
                    if not os.path.exists(dst_f):
                        try:
                            shutil.copy2(src_f, dst_f)
                        except Exception:
                            pass
                            
        configs_dir = os.path.join(config_dir, "configs")
        models_dir = os.path.join(config_dir, "models")
        os.makedirs(configs_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)

        root_configs = ["supporttargetlang.yaml", "api_profiles.json"]
        for f in root_configs:
            old_path = os.path.join(config_dir, f)
            new_path = os.path.join(configs_dir, f)
            if os.path.exists(old_path):
                try:
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                except Exception:
                    pass

    def _flatten_oldsession_structure(self, raw_oldsession: dict):
        """
        In-place flattening of oldsession nested settings for legacy compatibility during runtime.
        """
        if "current_settings" in raw_oldsession:
            flat_settings = {}
            for k, v in raw_oldsession["current_settings"].items():
                if isinstance(v, dict):
                    flat_settings.update(v)
                else:
                    flat_settings[k] = v
            raw_oldsession["current_settings"] = flat_settings
            
        if "job_queue" in raw_oldsession:
            for job in raw_oldsession["job_queue"]:
                if "settings" in job:
                    flat_settings = {}
                    for k, v in job["settings"].items():
                        if isinstance(v, dict):
                            flat_settings.update(v)
                        else:
                            flat_settings[k] = v
                    job["settings"] = flat_settings


