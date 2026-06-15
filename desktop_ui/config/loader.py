import os
import sys

class ConfigLoaderBase:
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
                "check_file": "app/translators/deepl.py",
                "check_module": "deepl"
            },
            "gemini": {
                "check_file": "app/translators/gemini.py",
                "check_module": "google.genai"
            },
            "deepseek": {
                "check_file": "app/translators/deepseek.py"
            },
            "groq": {
                "check_file": "app/translators/groq.py",
                "check_module": "groq"
            },
            "youdao": {
                "check_file": "app/translators/youdao.py"
            },
            "baidu": {
                "check_file": "app/translators/baidu.py"
            },
            "caiyun": {
                "check_file": "app/translators/caiyun.py"
            },
            "sakura": {
                "check_file": "app/translators/sakura.py"
            },
            "papago": {
                "check_file": "app/translators/papago.py"
            },
            "openai": {
                "check_file": "app/translators/openai.py",
                "check_module": "openai"
            },
            "custom_openai": {
                "check_file": "app/translators/custom_openai.py",
                "check_module": "openai"
            }
        },
        "ocr": {
            "32px": {"check_file": "models/ocr/alphabet-all-v7.txt"},
            "48px": {"check_file": "models/ocr/ocr_ar_48px.ckpt"},
            "48px_ctc": {"check_file": "models/ocr/ocr-ctc.ckpt"},
            "mocr": {
                "check_file": "app/ocr/mocr.py",
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
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        
        # Ensure directories exist and migrate old root files early
        config_dir = os.path.join(self.project_base_dir, ".config")
        configs_dir = os.path.join(config_dir, "configs")
        models_dir = os.path.join(config_dir, "models")
        os.makedirs(configs_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)

        root_configs = ["keys.yaml", "studio_config.yaml", "supporttargetlang.yaml", "api_profiles.json"]
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

        self.studio_config_path = os.path.join(configs_dir, "studio_config.yaml")

        # Load studio_config.yaml early
        import yaml
        self.studio_config = {}
        if os.path.exists(self.studio_config_path):
            try:
                with open(self.studio_config_path, "r", encoding="utf-8") as f:
                    self.studio_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading studio_config.yaml: {e}")

        # Load dict_profiles.yaml early
        self.dict_profiles_path = os.path.join(configs_dir, "dict_profiles.yaml")
        self.dict_profiles = {}
        if os.path.exists(self.dict_profiles_path):
            try:
                with open(self.dict_profiles_path, "r", encoding="utf-8") as f:
                    self.dict_profiles = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading dict_profiles.yaml: {e}")

        # Load languages from .config/langs/ early
        langs_dir = os.path.join(config_dir, "langs")
        os.makedirs(langs_dir, exist_ok=True)
        self.localization = {}
        if os.path.exists(langs_dir):
            try:
                for filename in os.listdir(langs_dir):
                    if filename.endswith(".yaml") or filename.endswith(".yml"):
                        lang_code = os.path.splitext(filename)[0]
                        file_path = os.path.join(langs_dir, filename)
                        with open(file_path, "r", encoding="utf-8") as f:
                            self.localization[lang_code] = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading files in langs directory: {e}")

        # Expose attributes from translator capabilities YAML
        capabilities_data = self._load_translator_capabilities()
        self.languages = self._load_backend_languages()
        
        self.translator_groups = capabilities_data.get("TRANSLATOR_GROUPS", {})
        self.log_colors = capabilities_data.get("LOG_COLORS", {
            "ERROR": "#E74C3C",
            "SUCCESS": "#2ECC71",
            "PIPELINE": "#5DADE2",
            "WARNING": "#F39C12",
            "INFO": "white",
            "DEBUG": "gray",
            "RAW": "gray"
        })
        self.translator_capabilities = capabilities_data.get("TRANSLATOR_CAPABILITIES", {})

        self.backend_schema = self._load_backend_schema()
        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # Run config initialization and repair before building data
        self._initialize_and_repair_config()

        self.ui_map = self._load_ui_map()
        self.tasks_config = self._load_tasks_config()

        self.app_language = self.studio_config.get("app_language", "English")
        self.localize_ui_map(self.app_language)

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
        self.full_config_data = self._build_full_config_data()

    def save_studio_config(self):
        import yaml
        try:
            with open(self.studio_config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.studio_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[ConfigLoader] Error saving studio_config.yaml: {e}")

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

    def _load_keys_file(self):
        """Loads variables from the keys.yaml file in the .config directory into a dict."""
        import yaml
        keys = {}
        keys_path = os.path.join(self.project_base_dir, ".config", "configs", "keys.yaml")
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
