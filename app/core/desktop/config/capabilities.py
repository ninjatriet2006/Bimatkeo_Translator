"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.config.capabilities
- RESPONSIBILITY: capabilities.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.config.capabilities.
=============================================================================
"""
# type: ignore
import os
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
import json
import subprocess
import urllib.request
import time
from app.core.desktop.constants import *


GLOBAL_ISO_MAP = {
    "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
    "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
    "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
    "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
    "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
    "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
}

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    class _CapabilitiesMixinBase:
        project_base_dir: str
        all_model_fields: list[str]
        required_model_fields: list[str]
else:
    _CapabilitiesMixinBase = object

class CapabilitiesMixin(_CapabilitiesMixinBase):
    project_base_dir: str
    localization: dict
    system_prompts: dict
    _DEFAULT_CHECKS: dict
    
    @property
    def _tesseract_langs_cache(self):
        if not hasattr(self, '_tess_langs'):
            try:
                import pytesseract
                self._tess_langs = pytesseract.get_languages()
            except Exception:
                self._tess_langs = []
        return self._tess_langs

    def _initialize_and_repair_config(self) -> None: pass
    def _load_translator_capabilities(self):
        """Returns translator groups + capabilities derived from the model registry (single source of truth)."""
        reg_groups = getattr(self, "registry_translator_groups", None)
        reg_caps = getattr(self, "registry_translator_capabilities", None)
        if reg_groups and reg_caps:
            print("[ConfigLoader] Loaded translator groups/capabilities from model registry.")
            return {
                "TRANSLATOR_GROUPS": reg_groups,
                "LOG_COLORS": self._default_log_colors(),
            }

        # Tự động lấy danh sách model từ registry (single source of truth)
        if hasattr(self, 'model_registry'):
            offline_keys = list(self.model_registry.get("offline_translator", {}).keys())
            ai_keys = list(self.model_registry.get("ai_translator", {}).keys())
        else:
            offline_keys = []
            ai_keys = []

        print("[ConfigLoader] Registry groups unavailable; using minimal default capabilities.")
        return {
            "TRANSLATOR_GROUPS": {
                CAT_OFFLINE_MODELS: offline_keys,
                CAT_API_BASED: ai_keys,
                CAT_OTHER_ACTIONS: [
                    "original",
                    "none"
                ]
            },
            "LOG_COLORS": self._default_log_colors()
        }

    def _default_log_colors(self):
        return {
            "ERROR": "#E74C3C",
            "SUCCESS": "#2ECC71",
            "PIPELINE": "#5DADE2",
            "WARNING": "#F39C12",  # Orange
            "INFO": "default",
            "DEBUG": "gray",
            "RAW": "gray"
        }

    def _load_backend_languages(self):
        """Loads languages dynamically from .config/configs/supporttargetlang.yaml, falling back to constants if unavailable."""
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "supporttargetlang.yaml")
        try:
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    langs = yaml.load(f)
                if isinstance(langs, dict):
                    formatted_langs = {}
                    for code, name in langs.items():
                        formatted_langs[str(name)] = str(code)
                    print("[ConfigLoader] Loaded languages dynamically from supporttargetlang.yaml.")
                    return formatted_langs
        except Exception as e:
            print(f"[ConfigLoader] Error loading supporttargetlang.yaml: {e}")

        return {
            "Auto-Detect": "auto",
            "English": "ENG",
            "Turkish": "TRK",
            "Japanese": "JPN",
            "Korean": "KOR",
            "Simplified Chinese": "CHS",
            "Traditional Chinese": "CHT",
            "Spanish": "ESP",
            "French": "FRA",
            "German": "DEU",
            "Russian": "RUS",
            "Portuguese (Brazilian)": "PTB",
            "Italian": "ITA",
            "Polish": "POL",
            "Dutch": "NLD",
            "Czech": "CSY",
            "Hungarian": "HUN",
            "Romanian": "ROM",
            "Ukrainian": "UKR",
            "Vietnamese": "VIN",
            "Arabic": "ARA",
            "Serbian": "SRP",
            "Croatian": "HRV",
            "Thai": "THA",
            "Indonesian": "IND",
            "Filipino (Tagalog)": "FIL"
        }

    def check_model_existence(self, model_name, field=None):
        """Checks if a model has its proof of existence."""
        if not isinstance(model_name, str):
            return True
        
        if model_name.lower() in ["none", "original", "auto"]:
            return True

        if model_name.startswith("tesseract_"):
            lang = model_name.replace("tesseract_", "")
            required_langs = []
            if lang == "mixed" or lang == "all_horizontal":
                required_langs = ["jpn", "jpn_vert", "chi_sim", "chi_sim_vert", "chi_tra", "chi_tra_vert", "kor", "kor_vert"]
            else:
                required_langs = [lang]
            
            tess_langs = self._tesseract_langs_cache
            for req in required_langs:
                if req not in tess_langs:
                    return False
            return True

        if field:
            field_key = field.lower()
            if field_key == "app_language":
                lang_data = None
                for code, data in self.localization.items():
                    if isinstance(data, dict) and data.get("language_name") == model_name:
                        lang_data = data
                        break
                if lang_data and isinstance(lang_data, dict):
                    if "settings" in lang_data or "tabs" in lang_data:
                        return True
                return False
                
            elif field_key == "system_prompt_profile":
                profiles = self.system_prompts.get("profiles", {})
                profile_data = None
                if isinstance(profiles, dict) and model_name in profiles:
                    profile_data = profiles[model_name]
                elif isinstance(self.system_prompts, dict) and model_name in self.system_prompts:
                    profile_data = self.system_prompts[model_name]
                if isinstance(profile_data, dict):
                    if "role_description" in profile_data or "json_schema_rules" in profile_data:
                        return True
                return False

            # Check against all dynamically loaded fields
            checkable_fields = self.all_model_fields
            if field_key not in checkable_fields:
                return True

        rule = None
        if field:
            field_key = field.lower()
            if hasattr(self, '_model_checks') and field_key in self._model_checks and model_name in self._model_checks[field_key]:
                rule = self._model_checks[field_key][model_name]
            elif field_key in self._DEFAULT_CHECKS and model_name in self._DEFAULT_CHECKS[field_key]:
                rule = self._DEFAULT_CHECKS[field_key][model_name]
        else:
            if hasattr(self, '_model_checks'):
                for f_key, models in self._model_checks.items():
                    if model_name in models:
                        rule = models[model_name]
                        break
            if not rule:
                for f_key, models in self._DEFAULT_CHECKS.items():
                    if model_name in models:
                        rule = models[model_name]
                        break
        
        if rule is None:
            if field and field.lower() == "ai_translator":
                return True
            return False

        check_module = rule.get("check_module")
        if check_module:
            import importlib.util
            modules = [check_module] if isinstance(check_module, str) else check_module
            for module_name in modules:
                try:
                    if importlib.util.find_spec(module_name) is None:
                        return False
                except Exception:
                    return False

        check_file = rule.get("check_file")
        if check_file and str(check_file).lower() != "none":
            files_to_check = [check_file]
            
            found = False
            for f in files_to_check:
                paths_to_try = [
                    os.path.join(self.project_base_dir, f),
                    os.path.abspath(f)
                ]
                for p in paths_to_try:
                    if os.path.exists(p):
                        if os.path.isdir(p):
                            try:
                                if len(os.listdir(p)) > 0:
                                    found = True
                                    break
                            except Exception:
                                pass
                        else:
                            found = True
                            break
                if found:
                    break
            if not found:
                return False

        return True

    def save_languages_config(self, lang_data):
        """Saves a languages dictionary {Name: Code} back to supporttargetlang.yaml."""
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "supporttargetlang.yaml")
        db_format = {str(code): str(name) for name, code in lang_data.items()}
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(db_format, f)
            self.languages = lang_data
            self._initialize_and_repair_config()
            return True
        except Exception as e:
            print(f"[ConfigLoader] Error saving supporttargetlang.yaml: {e}")
            return False




