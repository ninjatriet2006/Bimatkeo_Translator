import os
import json
import subprocess
import sys
import re

class ConfigLoader:
    _DEFAULT_CHECKS = {
        "offline_translator": {
            "sugoi": {"check_file": "models/translators/sugoi/spm.ja.nopretok.model"},
            "m2m100": {"check_file": "models/translators/m2m_100/m2m100_12b/sentencepiece.model"},
            "m2m100_big": {"check_file": "models/translators/m2m_100/m2m100_12b/model.bin"},
            "nllb": {"check_file": "models/translators/m2m_100/m2m100_12b/sentencepiece.model"},
            "nllb_big": {"check_file": "models/translators/m2m_100/m2m100_12b/model.bin"},
            "mbart50": {"check_file": "models/translators/m2m_100/m2m100_12b/sentencepiece.model"},
            "jparacrawl": {"check_file": "models/translators/jparacrawl/spm.ja.nopretok.model"},
            "jparacrawl_big": {"check_file": "models/translators/jparacrawl/spm.ja.nopretok.model"},
            "qwen2": {"check_file": "models/translators/qwen2/qwen2_1.5b/model.bin"},
            "qwen2_big": {"check_file": "models/translators/qwen2/qwen2_1.5b/model.bin"},
            "offline": {"check_file": "models/translators/m2m_100/m2m100_12b/sentencepiece.model"},
        },
        "ai_translator": {
            "deepl": {
                "check_file": "manga_translator/translators/deepl.py",
                "check_module": "deepl"
            },
            "gemini": {
                "check_file": "manga_translator/translators/gemini.py",
                "check_module": "google.genai"
            },
            "deepseek": {
                "check_file": "manga_translator/translators/deepseek.py"
            },
            "groq": {
                "check_file": "manga_translator/translators/groq.py",
                "check_module": "groq"
            },
            "youdao": {
                "check_file": "manga_translator/translators/youdao.py"
            },
            "baidu": {
                "check_file": "manga_translator/translators/baidu.py"
            },
            "caiyun": {
                "check_file": "manga_translator/translators/caiyun.py"
            },
            "sakura": {
                "check_file": "manga_translator/translators/sakura.py"
            },
            "papago": {
                "check_file": "manga_translator/translators/papago.py"
            },
            "openai": {
                "check_file": "manga_translator/translators/chatgpt.py",
                "check_module": "openai"
            },
            "custom_openai": {
                "check_file": "manga_translator/translators/custom_openai.py",
                "check_module": "openai"
            }
        },
        "ocr": {
            "32px": {"check_file": "models/ocr/alphabet-all-v7.txt"},
            "48px": {"check_file": "models/ocr/ocr_ar_48px.ckpt"},
            "48px_ctc": {"check_file": "models/ocr/ocr-ctc.ckpt"},
            "mocr": {
                "check_file": "manga_translator/ocr/model_manga_ocr.py",
                "check_module": "manga_ocr"
            }
        },
        "detector": {
            "default": {"check_file": "models/detection/detect-20241225.ckpt"},
            "dbconvnext": {"check_file": "models/detection/dbnet_convnext.ckpt"},
            "ctd": {"check_file": "models/detection/detect-20241225.ckpt"},
            "craft": {"check_file": "models/detector/craft/craft_mlt_25k.pth"},
            "paddle": {"check_file": "models/detector/paddle/det.onnx"},
        },
        "inpainter": {
            "default": {"check_file": "models/inpainting/lama_large_512px.ckpt"},
            "lama_large": {"check_file": "models/inpainting/lama_large_512px.ckpt"},
            "lama_mpe": {"check_file": "models/inpainting/inpainting_lama_mpe.ckpt"},
        },
        "upscaler": {
            "waifu2x": {"check_file": "models/waifu2x-linux/waifu2x-ncnn-vulkan"},
            "esrgan": {"check_file": "models/esrgan-linux/realesrgan-ncnn-vulkan"},
        },
        "colorizer": {
            "mc2": {"check_file": "models/manga-colorization-v2/generator.zip"},
        }
    }


    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = self._find_python_executable()
        self.cache_path = os.path.join(self.project_base_dir, "MangaStudio_Data", "temp", "schema_cache.json")

        self.backend_schema = self._load_backend_schema()
        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # Run config initialization and repair before building data
        self._initialize_and_repair_config()

        self.ui_map = self._load_ui_map()
        self.tasks_config = self._load_tasks_config()

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
        self.full_config_data = self._build_full_config_data()
        self.languages = self._load_backend_languages()

    def _find_python_executable(self):
        venv_path_win = os.path.join(self.project_base_dir, 'venv', 'Scripts', 'python.exe')
        venv_path_unix = os.path.join(self.project_base_dir, 'venv', 'bin', 'python')
        venv_path_sibling_unix = os.path.join(self.project_base_dir, '..', 'venv', 'bin', 'python')
        venv_path_sibling_win = os.path.join(self.project_base_dir, '..', 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_path_win):
            return venv_path_win
        elif os.path.exists(venv_path_unix):
            return venv_path_unix
        elif os.path.exists(venv_path_sibling_win):
            return venv_path_sibling_win
        elif os.path.exists(venv_path_sibling_unix):
            return venv_path_sibling_unix
        return sys.executable

    def _load_backend_schema(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    print("[ConfigLoader] Loading schema from cache...")
                    return json.load(f)
            except Exception:
                pass

        print("[ConfigLoader] Fetching fresh configuration schema...")
        try:
            sibling_dir = os.path.abspath(os.path.join(self.project_base_dir, "..", "manga-image-translator"))
            env = os.environ.copy()
            if os.path.exists(sibling_dir):
                env["PYTHONPATH"] = sibling_dir + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")

            command = [self.python_executable, "-m", "manga_translator", "config-help"]
            result = subprocess.run(command, env=env, capture_output=True, text=True, encoding='utf-8', check=True)
            schema_data = self._parse_schema_output(result.stdout)
            if schema_data is None:
                raise ValueError("Schema command did not return valid JSON.")
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4)
            return schema_data
        except Exception as e:
            print(f"[ERROR] Could not fetch schema: {e}")
            return None
    
    def _parse_schema_output(self, stdout):
        """Extracts the JSON portion of the schema output."""
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            cleaned_stdout = self._strip_ansi(stdout)
            json_start = cleaned_stdout.find('{')
            json_end = cleaned_stdout.rfind('}')
            if json_start == -1 or json_end == -1 or json_end < json_start:
                return None
            try:
                return json.loads(cleaned_stdout[json_start:json_end + 1])
            except json.JSONDecodeError:
                return None

    def _strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B\[[0-9;]*[A-Za-z]')
        return ansi_escape.sub('', text)

    def _load_ui_map(self):
        map_path = os.path.join(self.project_base_dir, 'MangaStudio_Data', 'ui_map.json')
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] UI map loading failed: {e}")
            return {}

    def _load_tasks_config(self):
        """Loads the special tasks configuration from tasks.json."""
        tasks_path = os.path.join(self.project_base_dir, 'MangaStudio_Data', 'tasks.json')
        try:
            with open(tasks_path, 'r', encoding='utf-8') as f:
                print("[ConfigLoader] Loading tasks configuration...")
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] tasks.json not found at: {tasks_path}")
            return {}
        except Exception as e:
            print(f"[ERROR] Tasks config loading failed: {e}")
            return {}
    
    def _get_definition_from_ref(self, ref_path):
        try:
            parts = ref_path.split('/')[1:]
            node = self.backend_schema
            for part in parts:
                node = node[part]
            return node
        except Exception:
            return None

    def _parse_factory_defaults(self):
        """Deep-parses the schema to get ALL default values, including nested ones."""
        if not self.backend_schema:
            return {}
        defaults = {}
        properties = self.backend_schema.get("properties", {})

        for prop_key, prop_value in properties.items():
            if "default" in prop_value and isinstance(prop_value.get("default"), dict):
                defaults.update(prop_value["default"])
            elif "default" in prop_value:
                defaults[prop_key] = prop_value["default"]
        return defaults

    def _build_full_config_data(self):
        """Builds the final, merged config data for the UI, reading ALL properties."""
        if not self.ui_map:
            return {}
        full_data = {}
        all_properties = {}

        # 1. Gather all root-level properties
        root_props = self.backend_schema.get("properties", {})
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

            # Use the already parsed factory default if it exists
            if key in self.factory_defaults:
                merged_info['default'] = self.factory_defaults[key]

            # Add enum values (for dropdowns) if they exist
            prop_def = all_properties.get(key)
            if prop_def and isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)
                    if enum_def and "enum" in enum_def:
                        # Load custom choices if config file exists, else use schema enums
                        custom_choices = self._load_custom_models(key)
                        merged_info['values'] = custom_choices if custom_choices is not None else enum_def["enum"]
            
            # --- NEW: Manually handle UI-only enum settings offline_translator and ai_translator ---
            if key in ['offline_translator', 'ai_translator']:
                custom_choices = self._load_custom_models(key)
                if custom_choices is not None:
                    merged_info['values'] = custom_choices

            full_data[key] = merged_info

        return full_data

    def get_tasks_config(self):
        """Returns the loaded tasks configuration."""
        return self.tasks_config

    def get_factory_defaults(self):
        defaults = self.factory_defaults.copy()
        # Merge defaults from ui_map.json for UI-only settings
        for key, ui_info in self.ui_map.items():
            if not key.startswith("__") and "default" in ui_info:
                if key not in defaults:
                    defaults[key] = ui_info["default"]
        return defaults

    def get_tab_order(self):
        return self.ui_map.get("__tab_order__", [])

    def _load_backend_languages(self):
        """Loads languages dynamically from .config/supporttargetlang.yaml, falling back to constants if unavailable."""
        import yaml
        yaml_path = os.path.join(self.project_base_dir, ".config", "supporttargetlang.yaml")
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

        # Fallback to static constants if YAML load failed
        try:
            from desktop_ui.constants import LANGUAGES as STATIC_LANGUAGES
        except ImportError:
            STATIC_LANGUAGES = {"Auto-Detect": "auto"}
        return STATIC_LANGUAGES

    def _initialize_and_repair_config(self):
        """
        Ensures that .config/ exists and contains validated, repaired YAML files
        for languages (supporttargetlang.yaml) and all backend enum models (model_ocr.yaml, etc.).
        """
        import yaml
        config_dir = os.path.join(self.project_base_dir, ".config")
        os.makedirs(config_dir, exist_ok=True)

        # 1. Repair supporttargetlang.yaml
        lang_yaml_path = os.path.join(config_dir, "supporttargetlang.yaml")
        old_lang_path = os.path.join(config_dir, "lang.yaml")
        
        try:
            from desktop_ui.constants import LANGUAGES as STATIC_LANGUAGES
            default_langs = {str(v): str(k) for k, v in STATIC_LANGUAGES.items()}
        except Exception:
            default_langs = {"auto": "Auto-Detect", "ENG": "English"}

        loaded_langs = {}
        read_path = lang_yaml_path if os.path.exists(lang_yaml_path) else old_lang_path
        if os.path.exists(read_path):
            try:
                with open(read_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                if isinstance(content, dict):
                    for k, v in content.items():
                        if k and v and isinstance(k, (str, int, float)) and isinstance(v, (str, int, float)):
                            loaded_langs[str(k)] = str(v)
            except Exception as e:
                print(f"[ConfigLoader] Error reading lang config: {e}")

        # Auto-match & Repair: ensure all default codes are present
        repaired_langs = default_langs.copy()
        repaired_langs.update(loaded_langs)

        try:
            with open(lang_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(repaired_langs, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            if os.path.exists(old_lang_path) and lang_yaml_path != old_lang_path:
                os.remove(old_lang_path)
        except Exception as e:
            print(f"[ConfigLoader] Error writing supporttargetlang.yaml: {e}")

        # 2. Repair dynamic enum model files
        enum_fields = {}
        all_properties = {}

        root_props = self.backend_schema.get("properties", {})
        all_properties.update(root_props)
        for prop in root_props.values():
            ref_path = prop.get("allOf", [{}])[0].get('$ref')
            if ref_path:
                config_def = self._get_definition_from_ref(ref_path)
                if config_def and "properties" in config_def:
                    all_properties.update(config_def["properties"])

        for key, prop_def in all_properties.items():
            if isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)
                    if enum_def and "enum" in enum_def:
                        enum_fields[key] = enum_def["enum"]

        # Intercept and split translator enum field
        if 'translator' in enum_fields:
            del enum_fields['translator']

        try:
            from desktop_ui.constants import TRANSLATOR_GROUPS
        except ImportError:
            TRANSLATOR_GROUPS = {}

        enum_fields['offline_translator'] = TRANSLATOR_GROUPS.get("--- OFFLINE MODELS (No API Key) ---", [])
        enum_fields['ai_translator'] = TRANSLATOR_GROUPS.get("--- API-BASED (Requires Setup) ---", [])

        # Delete old model_translator.yaml if it exists
        old_translator_yaml = os.path.join(config_dir, "model_translator.yaml")
        if os.path.exists(old_translator_yaml):
            try:
                os.remove(old_translator_yaml)
            except Exception:
                pass

        # For each enum field, ensure .config/model_<field>.yaml exists and is repaired
        for field, schema_choices in enum_fields.items():
            model_yaml_path = os.path.join(config_dir, f"model_{field.lower()}.yaml")
            
            loaded_models = []
            if os.path.exists(model_yaml_path):
                try:
                    with open(model_yaml_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    if isinstance(content, dict) and "models" in content:
                        models_list = content["models"]
                    elif isinstance(content, list):
                        models_list = content
                    else:
                        models_list = []
                    
                    for item in models_list:
                        if isinstance(item, str):
                            loaded_models.append(item)
                        elif isinstance(item, dict) and "name" in item:
                            loaded_models.append(item)
                except Exception as e:
                    print(f"[ConfigLoader] Error reading model_{field.lower()}.yaml: {e}")

            # Create a dictionary of existing models by name to preserve checks
            existing_by_name = {}
            for item in loaded_models:
                if isinstance(item, str):
                    existing_by_name[item] = {"name": item}
                elif isinstance(item, dict) and "name" in item:
                    existing_by_name[item["name"]] = item

            # Merge with default choices
            repaired_models = []
            for item in schema_choices:
                name = str(item)
                field_key = field.lower()
                has_default = (field_key in self._DEFAULT_CHECKS and name in self._DEFAULT_CHECKS[field_key])
                
                if name in existing_by_name and not has_default:
                    repaired_models.append(existing_by_name[name])
                else:
                    model_entry = {"name": name}
                    if has_default:
                        model_entry.update(self._DEFAULT_CHECKS[field_key][name])
                    repaired_models.append(model_entry)
            
            # Add any extra items that user had defined in YAML but are not in schema_choices
            for name, item in existing_by_name.items():
                if name not in schema_choices:
                    repaired_models.append(item)

            try:
                with open(model_yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump({"models": repaired_models}, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            except Exception as e:
                print(f"[ConfigLoader] Error writing model_{field.lower()}.yaml: {e}")

    def _load_custom_models(self, field):
        """Loads custom models list from .config/model_<field>.yaml if it exists."""
        import yaml
        model_yaml_path = os.path.join(self.project_base_dir, ".config", f"model_{field.lower()}.yaml")
        try:
            if os.path.exists(model_yaml_path):
                with open(model_yaml_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                models_list = []
                if isinstance(content, dict) and "models" in content:
                    models_list = content["models"]
                elif isinstance(content, list):
                    models_list = content
                
                # Register checks
                self.register_model_checks(field, models_list)
                
                names = []
                for item in models_list:
                    if isinstance(item, str):
                        names.append(item)
                    elif isinstance(item, dict) and "name" in item:
                        names.append(str(item["name"]))
                return names
        except Exception as e:
            print(f"[ConfigLoader] Error reading custom models for {field}: {e}")
        return None

    def register_model_checks(self, field, model_list):
        if not hasattr(self, '_model_checks'):
            self._model_checks = {}
        field_key = field.lower()
        if field_key not in self._model_checks:
            self._model_checks[field_key] = {}
        for item in model_list:
            if isinstance(item, dict) and "name" in item:
                name = item["name"]
                self._model_checks[field_key][name] = {
                    "check_file": item.get("check_file"),
                    "check_module": item.get("check_module")
                }

    def check_model_existence(self, model_name, field=None):
        """Checks if a model has its proof of existence."""
        if not isinstance(model_name, str):
            return True
        
        if model_name.lower() in ["none", "original", "auto", "default"]:
            return True

        # Retrieve check rule: custom from YAML first, then default
        rule = None
        if field:
            field_key = field.lower()
            if hasattr(self, '_model_checks') and field_key in self._model_checks and model_name in self._model_checks[field_key]:
                rule = self._model_checks[field_key][model_name]
            elif field_key in self._DEFAULT_CHECKS and model_name in self._DEFAULT_CHECKS[field_key]:
                rule = self._DEFAULT_CHECKS[field_key][model_name]
        else:
            # Fallback searching all fields if field is not provided
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

        # 1. Check Python module dependency if required
        check_module = rule.get("check_module")
        if check_module:
            modules = [check_module] if isinstance(check_module, str) else check_module
            for module_name in modules:
                try:
                    __import__(module_name)
                except ImportError:
                    return False

        # 2. Check physical files/weights dependency
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
            
            sibling_dir = os.path.abspath(os.path.join(self.project_base_dir, "..", "manga-image-translator"))
            found = False
            for f in files_to_check:
                paths_to_try = [
                    os.path.join(sibling_dir, f),
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


    def _load_keys_file(self):
        """Loads variables from the keys.yaml file in the .config directory into a dict."""
        import yaml
        keys = {}
        keys_path = os.path.join(self.project_base_dir, ".config", "keys.yaml")
        if os.path.exists(keys_path):
            try:
                with open(keys_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                if isinstance(content, dict):
                    for k, v in content.items():
                        if k and isinstance(k, str):
                            keys[k] = str(v) if v is not None else ""
            except Exception as e:
                print(f"[ConfigLoader] Error loading keys.yaml: {e}")
        return keys

    def get_env_var(self, name):
        """Returns the value of an environment variable, checking keys.yaml first then os.environ."""
        self._keys_vars = self._load_keys_file()
        return self._keys_vars.get(name) or os.environ.get(name)


