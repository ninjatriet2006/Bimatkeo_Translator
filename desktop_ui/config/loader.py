# type: ignore
import os
import sys

_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")
_exe_ext = ".exe" if _os_suffix == "win" else ""

class ConfigLoaderBase:
    # NOTE: _DEFAULT_CHECKS is now DERIVED from the model registry at runtime
    # (see RegistryMixin.load_registry, called early in __init__, which sets
    # self._DEFAULT_CHECKS as an instance attribute). This class-level value is
    # only a safe empty fallback so attribute access never raises if the
    # registry hasn't loaded yet. Do NOT add model definitions here -- the
    # single source of truth is .config/models/model_registry.yaml.
    _DEFAULT_CHECKS = {}

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
        self.oldsession_path = os.path.join(configs_dir, "oldsession.yaml")

        # Load studio_config.yaml early
        import yaml
        self.studio_config = {}
        if os.path.exists(self.studio_config_path):
            try:
                with open(self.studio_config_path, "r", encoding="utf-8") as f:
                    self.studio_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading studio_config.yaml: {e}")

        # Load oldsession.yaml for UI session state
        self.oldsession_config = {}
        if os.path.exists(self.oldsession_path):
            try:
                with open(self.oldsession_path, "r", encoding="utf-8") as f:
                    self.oldsession_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading oldsession.yaml: {e}")

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

        # Load the model registry FIRST (single source of truth).
        # This derives self._DEFAULT_CHECKS and registry-based groups/capabilities
        # before repair/capabilities/schema logic consumes them.
        self.load_registry()

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

        # Run the one-time model fallback sweep (once per machine). Repairs any
        # stored profile/default that points at a deleted or not-set-up model.
        # No-op after the first successful run on this machine. Never raises.
        self.optimize_profiles_once()

    def save_studio_config(self):
        import yaml
        try:
            with open(self.studio_config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.studio_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[ConfigLoader] Error saving studio_config.yaml: {e}")

    def save_oldsession_config(self):
        import yaml
        try:
            with open(self.oldsession_path, "w", encoding="utf-8") as f:
                yaml.dump(self.oldsession_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[ConfigLoader] Error saving oldsession.yaml: {e}")

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
