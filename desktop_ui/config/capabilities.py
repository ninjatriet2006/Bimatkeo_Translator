import os
import yaml
import json
import subprocess
import urllib.request
import time

class CapabilitiesMixin:
    def _load_translator_capabilities(self):
        """Loads translator capabilities and groups dynamically from translator_capabilities.yaml, falling back to defaults if unavailable."""
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "translator_capabilities.yaml")
        
        default_capabilities = {
            "TRANSLATOR_GROUPS": {
                "--- OFFLINE MODELS (No API Key) ---": [
                    "sugoi", "m2m100", "m2m100_big", "nllb", "nllb_big", "mbart50",
                    "jparacrawl", "jparacrawl_big", "qwen2", "qwen2_big", "offline"
                ],
                "--- API-BASED (Requires Setup) ---": [
                    "deepl", "gemini", "deepseek", "groq", "youdao", "baidu",
                    "caiyun", "sakura", "papago", "openai", "custom_openai"
                ],
                "--- OTHER ACTIONS ---": [
                    "original",
                    "none"
                ]
            },
            "TRANSLATOR_CAPABILITIES": {
                "deepl": {"__any__": "__all__"},
                "gemini": {"__any__": "__all__"},
                "deepseek": {"__any__": "__all__"},
                "groq": {"__any__": "__all__"},
                "youdao": {"__any__": "__all__"},
                "baidu": {"__any__": "__all__"},
                "caiyun": {"__any__": "__all__"},
                "openai": {"__any__": "__all__"},
                "custom_openai": {"__any__": "__all__"},
                "papago": {
                    "KOR": ["ENG", "JPN", "CHS", "CHT", "FRA", "DEU", "RUS", "ESP", "ITA", "VIE", "THA", "IND"],
                    "JPN": ["ENG", "KOR", "CHS", "CHT"],
                    "CHS": ["ENG", "KOR", "JPN"],
                    "CHT": ["ENG", "KOR", "JPN"],
                    "ENG": ["KOR", "JPN", "CHS", "CHT", "FRA", "DEU", "ESP", "ITA"],
                    "FRA": ["ENG", "KOR"],
                    "ESP": ["ENG", "KOR"],
                    "ITA": ["ENG", "KOR"],
                    "DEU": ["ENG", "KOR"]
                },
                "sakura": {
                    "JPN": ["CHS", "CHT"],
                    "CHS": ["JPN"],
                    "CHT": ["JPN"]
                },
                "sugoi": {
                    "JPN": ["ENG"]
                },
                "jparacrawl": {
                    "JPN": ["ENG"]
                },
                "jparacrawl_big": {
                    "JPN": ["ENG"]
                },
                "nllb": {"__any__": "__all__"},
                "nllb_big": {"__any__": "__all__"},
                "m2m100": {"__any__": "__all__"},
                "m2m100_big": {"__any__": "__all__"},
                "mbart50": {"__any__": "__all__"},
                "qwen2": {"__any__": "__all__"},
                "qwen2_big": {"__any__": "__all__"},
                "offline": {"__any__": "__all__"},
                "original": {},
                "none": {}
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
        
        if not os.path.exists(yaml_path):
            try:
                os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_capabilities, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                print("[ConfigLoader] Created default translator_capabilities.yaml")
            except Exception as e:
                print(f"[ConfigLoader] Error creating translator_capabilities.yaml: {e}")
                return default_capabilities

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)
            if isinstance(loaded, dict) and "TRANSLATOR_GROUPS" in loaded and "TRANSLATOR_CAPABILITIES" in loaded:
                print("[ConfigLoader] Loaded translator capabilities dynamically from translator_capabilities.yaml.")
                return loaded
        except Exception as e:
            print(f"[ConfigLoader] Error loading translator_capabilities.yaml: {e}")
            
        return default_capabilities

    def _load_backend_languages(self):
        """Loads languages dynamically from .config/configs/supporttargetlang.yaml, falling back to constants if unavailable."""
        yaml_path = os.path.join(self.project_base_dir, ".config", "configs", "supporttargetlang.yaml")
        try:
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    langs = yaml.safe_load(f)
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
                
            elif field_key == "dict_profile":
                profiles = self.dict_profiles.get("profiles", {})
                profile_data = None
                if isinstance(profiles, dict) and model_name in profiles:
                    profile_data = profiles[model_name]
                elif isinstance(self.dict_profiles, dict) and model_name in self.dict_profiles:
                    profile_data = self.dict_profiles[model_name]
                if isinstance(profile_data, dict):
                    if "pre_dict" in profile_data or "post_dict" in profile_data or "gpt_config" in profile_data:
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
            modules = [check_module] if isinstance(check_module, str) else check_module
            for module_name in modules:
                try:
                    cmd = [self.python_executable, "-c", f"import {module_name}"]
                    res = subprocess.run(cmd, capture_output=True, timeout=5)
                    if res.returncode != 0:
                        return False
                except Exception:
                    return False

        check_file = rule.get("check_file")
        if check_file:
            files_to_check = [check_file]
            if model_name == "waifu2x":
                files_to_check = [
                    "models/waifu2x-linux/waifu2x-ncnn-vulkan",
                    "models/waifu2x-win/waifu2x-ncnn-vulkan.exe",
                    "models/waifu2x-macos/waifu2x-ncnn-vulkan"
                ]
            elif model_name == "esrgan":
                files_to_check = [
                    "models/esrgan-linux/realesrgan-ncnn-vulkan",
                    "models/esrgan-win/realesrgan-ncnn-vulkan.exe",
                    "models/esrgan-macos/realesrgan-ncnn-vulkan"
                ]
            
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
                yaml.dump(db_format, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
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
                yaml.dump(capabilities_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            self.translator_groups = capabilities_data.get("TRANSLATOR_GROUPS", {})
            self.translator_capabilities = capabilities_data.get("TRANSLATOR_CAPABILITIES", {})
            self.log_colors = capabilities_data.get("LOG_COLORS", self.log_colors)
            self._initialize_and_repair_config()
            return True
        except Exception as e:
            print(f"[ConfigLoader] Error saving translator_capabilities.yaml: {e}")
            return False

    def fetch_online_languages_libretranslate(self):
        """Fetches supported target languages from public LibreTranslate API mirrors."""
        urls = [
            "https://translate.argosopentech.com/languages",
            "https://libretranslate.com/languages"
        ]
        
        last_error = None
        data = None
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode('utf-8'))
                if data:
                    break
            except Exception as e:
                last_error = e
                continue
                
        if not data:
            raise RuntimeError(f"Failed to fetch languages from LibreTranslate API: {last_error}")
            
        ISO_MAP = {
            "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
            "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
            "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
            "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
            "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
            "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
        }
        
        langs_dict = {}
        for item in data:
            code = item.get("code")
            name = item.get("name")
            if code and name:
                app_code = ISO_MAP.get(code.lower(), code.upper())
                langs_dict[str(name)] = str(app_code)
                
        return langs_dict

    def fetch_online_languages_lingva(self):
        """Fetches supported languages from Lingva Translate API (a public frontend for Google Translate)."""
        url = "https://lingva.ml/api/v1/languages"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            raise RuntimeError(f"Failed to fetch languages from Lingva API: {e}")
            
        ISO_MAP = {
            "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
            "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
            "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
            "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
            "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
            "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
        }
        
        langs_dict = {}
        languages_list = data.get("languages", []) or data.get("targets", [])
        if not languages_list and isinstance(data, list):
            languages_list = data
            
        for item in languages_list:
            code = item.get("code")
            name = item.get("name")
            if code and name:
                app_code = ISO_MAP.get(code.lower(), code.upper())
                langs_dict[str(name)] = str(app_code)
                
        return langs_dict

    def update_single_translator_capabilities(self, translator_name, api_key=None):
        """
        Updates target language capabilities for a single translator.
        If api_key is provided for online translators (like DeepL), calls the real API.
        Otherwise, uses a mock implementation to simulate fetching updated capabilities from online.
        """
        translator_name = translator_name.lower()
        
        if translator_name == "deepl" and api_key:
            host = "api-free.deepl.com" if "-free" in api_key.lower() or len(api_key) < 40 else "api.deepl.com"
            url = f"https://{host}/v2/languages?type=target"
            try:
                req = urllib.request.Request(url, headers={
                    'Authorization': f'DeepL-Auth-Key {api_key}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                })
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                ISO_MAP = {
                    "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
                    "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
                    "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
                    "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
                    "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
                    "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
                }
                supported_targets = []
                for item in data:
                    lang_code = item.get("language", "").lower()
                    base_code = lang_code.split("-")[0]
                    app_code = ISO_MAP.get(base_code, base_code.upper())
                    if app_code not in supported_targets:
                        supported_targets.append(app_code)
                
                if supported_targets:
                    capabilities_data = self._load_translator_capabilities()
                    capabilities_data.setdefault("TRANSLATOR_CAPABILITIES", {})
                    capabilities_data["TRANSLATOR_CAPABILITIES"]["deepl"] = {"__any__": supported_targets}
                    self.save_capabilities_config(capabilities_data)
                    return True, f"Successfully updated DeepL target languages: {len(supported_targets)} languages supported."
            except Exception as e:
                return False, f"Failed to call DeepL API: {e}"
        
        time.sleep(1.0) # Simulate network delay
        
        capabilities_data = self._load_translator_capabilities()
        capabilities_data.setdefault("TRANSLATOR_CAPABILITIES", {})
        
        if translator_name in capabilities_data["TRANSLATOR_CAPABILITIES"]:
            curr_caps = capabilities_data["TRANSLATOR_CAPABILITIES"][translator_name]
            
            if isinstance(curr_caps, dict):
                if curr_caps.get("__any__") == "__all__":
                    return True, f"Translator '{translator_name}' supports all languages. Configuration is already up-to-date."
                else:
                    updated = False
                    for src, dsts in list(curr_caps.items()):
                        if isinstance(dsts, list) and "MOK" not in dsts:
                            dsts.append("MOK")
                            updated = True
                    
                    if not updated:
                        curr_caps["__any__"] = ["ENG", "VIN", "JPN", "MOK"]
                    
                    capabilities_data["TRANSLATOR_CAPABILITIES"][translator_name] = curr_caps
                    self.save_capabilities_config(capabilities_data)
                    return True, f"Mock Update: Successfully simulated update for '{translator_name}'. Added mock test code 'MOK'."
            else:
                capabilities_data["TRANSLATOR_CAPABILITIES"][translator_name] = {"__any__": ["ENG", "VIN", "JPN", "MOK"]}
                self.save_capabilities_config(capabilities_data)
                return True, f"Mock Update: Reinitialized capabilities for '{translator_name}' with test set."
        else:
            capabilities_data["TRANSLATOR_CAPABILITIES"][translator_name] = {"__any__": ["ENG", "VIN", "JPN", "MOK"]}
            self.save_capabilities_config(capabilities_data)
            return True, f"Mock Update: Created capabilities map for '{translator_name}'."
