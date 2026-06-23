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
from desktop_ui.constants import *


GLOBAL_ISO_MAP = {
    "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
    "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
    "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
    "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
    "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
    "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
}

class CapabilitiesMixin:
    project_base_dir: str
    localization: dict
    system_prompts: dict
    _DEFAULT_CHECKS: dict
    def _initialize_and_repair_config(self) -> None: pass
    def _load_translator_capabilities(self):
        """Returns translator groups + capabilities.

        Priority: data derived from the model registry (single source of truth).
        LOG_COLORS still comes from translator_capabilities.yaml if present.
        Falls back to a minimal hardcoded default only if the registry produced nothing.
        """
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "translator_capabilities.yaml")

        # 1. Read LOG_COLORS (and any extra) from the existing YAML, if available.
        yaml_data = {}
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.load(f)
                if isinstance(loaded, dict):
                    yaml_data = loaded
            except Exception as e:
                print(f"[ConfigLoader] Error loading translator_capabilities.yaml: {e}")

        # 2. Prefer registry-derived groups/capabilities (single source of truth).
        reg_groups = getattr(self, "registry_translator_groups", None)
        reg_caps = getattr(self, "registry_translator_capabilities", None)
        if reg_groups and reg_caps:
            print("[ConfigLoader] Loaded translator groups/capabilities from model registry.")
            return {
                "TRANSLATOR_GROUPS": reg_groups,
                "LOG_COLORS": yaml_data.get("LOG_COLORS", self._default_log_colors()),
            }

        default_capabilities = {
            "TRANSLATOR_GROUPS": {
                CAT_OFFLINE_MODELS: [
                    "m2m100", "m2m100_big", "nllb", "nllb_big", "mbart50",
                    "jparacrawl", "jparacrawl_big", "qwen2", "qwen2_big", "offline"
                ],
                CAT_API_BASED: [
                    "deepl", "gemini", "deepseek", "groq", "youdao", "baidu",
                    "caiyun", "sakura", "papago", "openai", "custom_openai"
                ],
                CAT_OTHER_ACTIONS: [
                    "original",
                    "none"
                ]
            },

            "LOG_COLORS": {
                "ERROR": "#E74C3C",
                "SUCCESS": "#2ECC71",
                "PIPELINE": "#5DADE2",
                "WARNING": "#F39C12",
                "INFO": "white",
                "DEBUG": "gray",
                "RAW": "gray"
            }
        }
        
        # Registry produced nothing usable; fall back to the legacy YAML if it
        # contains valid groups/capabilities, otherwise the minimal default.
        if isinstance(yaml_data, dict) and "TRANSLATOR_GROUPS" in yaml_data:
            print("[ConfigLoader] Registry unavailable; loaded capabilities from translator_capabilities.yaml.")
            return yaml_data

        print("[ConfigLoader] Registry and YAML unavailable; using minimal default capabilities.")
        return default_capabilities

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
                    if "pre_dict" in profile_data or "post_dict" in profile_data or "role_description" in profile_data or "json_schema_rules" in profile_data:
                        return True
                return False

            checkable_fields = {
                "offline_translator", "ai_translator", "detector", "ocr", "inpainter", "upscaler", "colorizer", "renderer"
            }
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
        
        if not rule:
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
        if check_file:
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

    def save_capabilities_config(self, capabilities_data):
        """Saves translator capabilities data back to translator_capabilities.yaml."""
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "translator_capabilities.yaml")
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(capabilities_data, f)
            self.translator_groups = capabilities_data.get("TRANSLATOR_GROUPS", {})
            self.log_colors = capabilities_data.get("LOG_COLORS", self.log_colors)
            self._initialize_and_repair_config()
            return True
        except Exception as e:
            print(f"[ConfigLoader] Error saving translator_capabilities.yaml: {e}")
            return False


