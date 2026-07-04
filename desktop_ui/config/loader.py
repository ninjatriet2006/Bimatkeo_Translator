# type: ignore
import os
import sys
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")
_exe_ext = ".exe" if _os_suffix == "win" else ""

from app.core.utils import get_python_executable
from app.core.base_config import BaseConfigLoader

from typing import Callable

class ConfigLoaderBase(BaseConfigLoader):
    _default_log_colors: Callable
    _build_full_config_data: Callable
    # NOTE: _DEFAULT_CHECKS is now DERIVED from the model registry at runtime
    # (see RegistryMixin.load_registry, called early in __init__, which sets
    # self._DEFAULT_CHECKS as an instance attribute). This class-level value is
    # only a safe empty fallback so attribute access never raises if the
    # registry hasn't loaded yet. Do NOT add model definitions here -- the
    # single source of truth is .config/models/model_registry.yaml.
    _DEFAULT_CHECKS = {}

    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = get_python_executable(self.project_base_dir)
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        
        # Ensure directories exist and migrate old root files early
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

        root_configs = ["studio_config.yaml", "supporttargetlang.yaml", "api_profiles.json"]
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

        # Load configs
        self.studio_config = self._load_yaml_file(self.studio_config_path)
        raw_oldsession = self._load_yaml_file(self.oldsession_path)
        
        # Flatten current_settings
        if "current_settings" in raw_oldsession:
            flat_settings = {}
            for k, v in raw_oldsession["current_settings"].items():
                if isinstance(v, dict):
                    flat_settings.update(v)
                else:
                    flat_settings[k] = v
            raw_oldsession["current_settings"] = flat_settings
            
        # Flatten job queue settings
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
                    
        self.oldsession_config = raw_oldsession
        
        self.system_prompts_path = os.path.join(configs_dir, "system_prompt.yaml")
        self.system_prompts = self._load_yaml_file(self.system_prompts_path)

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
                            self.localization[lang_code] = yaml.load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading files in langs directory: {e}")

        # Load the model registry FIRST (single source of truth).
        # This derives self._DEFAULT_CHECKS and registry-based groups/capabilities
        # before repair/capabilities/schema logic consumes them.
        self.load_registry()  # type: ignore

        # Expose attributes from translator capabilities YAML
        capabilities_data = self._load_translator_capabilities()  # type: ignore
        self.languages = self._load_backend_languages()  # type: ignore
        
        self.translator_groups = capabilities_data.get("TRANSLATOR_GROUPS", {})
        self.log_colors = capabilities_data.get("LOG_COLORS", self._default_log_colors())


        self.backend_schema = self._load_backend_schema()
        if not self.backend_schema:
            raise RuntimeError("Failed to load backend configuration schema.")

        # Run config initialization and repair before building data
        self._initialize_and_repair_config()  # type: ignore

        self.ui_map = self._load_ui_map()


        self.app_language = self.oldsession_config.get("app_language", self.studio_config.get("app_language", "English"))
        self.apply_language(self.app_language)  # type: ignore

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
        self.full_config_data = self._build_full_config_data()

        # Run the one-time model fallback sweep (once per machine). Repairs any
        # stored profile/default that points at a deleted or not-set-up model.
        # No-op after the first successful run on this machine. Never raises.
        self.optimize_profiles_once()  # type: ignore


    def save_oldsession_config(self):
        import copy
        data_to_save = copy.deepcopy(self.oldsession_config)
        
        def nest_settings(flat_dict):
            nested = {}
            for k, v in flat_dict.items():
                group = "Extra Settings"
                if hasattr(self, 'full_config_data') and k in self.full_config_data:
                    group = self.full_config_data[k].get("group", "Extra Settings")
                if group not in nested:
                    nested[group] = {}
                nested[group][k] = v
            return nested
            
        if "current_settings" in data_to_save and isinstance(data_to_save["current_settings"], dict):
            data_to_save["current_settings"] = nest_settings(data_to_save["current_settings"])
            
        if "job_queue" in data_to_save and isinstance(data_to_save["job_queue"], list):
            for job in data_to_save["job_queue"]:
                if "settings" in job and isinstance(job["settings"], dict):
                    job["settings"] = nest_settings(job["settings"])
                    
        # Add a critical AI rule comment at the top when saving
        if not hasattr(data_to_save, 'yaml_set_start_comment'):
            # Convert to ruamel.yaml.comments.CommentedMap if it's a plain dict
            from ruamel.yaml.comments import CommentedMap
            cm = CommentedMap(data_to_save)
            data_to_save = cm
            
        if hasattr(data_to_save, 'yaml_set_start_comment'):
            comment = """========================================================================
CRITICAL RULE FOR AI AGENTS (e.g. Gemini, GPT):
DO NOT USE FLAT DICTIONARIES FOR current_settings OR job_queue settings!
This configuration uses a NESTED structure. The UI Tabs are the root keys
(e.g., 'General & Translator'). All settings must be nested directly inside
their respective tab.
========================================================================"""
            data_to_save.yaml_set_start_comment(comment)

        self._save_yaml_file(self.oldsession_path, data_to_save)


    def get_factory_defaults(self):
        defaults = self.factory_defaults.copy()
        # Merge defaults from ui_map.json for UI-only settings
        for tab_name, widgets in self.ui_map.items():
            if isinstance(widgets, dict):
                for key, ui_info in widgets.items():
                    if isinstance(ui_info, dict) and "default" in ui_info:
                        defaults[key] = ui_info["default"]
        return defaults


    def get_env_var(self, name):
        """Returns the value of an environment variable."""
        return os.environ.get(name)
