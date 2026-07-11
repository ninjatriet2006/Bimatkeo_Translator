# type: ignore
import os
import sys
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")
_exe_ext = ".exe" if _os_suffix == "win" else ""

from app.core.base.env import get_python_executable
from app.core.base import BaseConfigLoader

from typing import Callable

class ConfigLoaderBase(BaseConfigLoader):
    _default_log_colors: Callable
    _build_full_config_data: Callable
    # NOTE: _DEFAULT_CHECKS is now DERIVED from the model registry at runtime
    # (see RegistryMixin.load_registry, called early in __init__, which sets
    # self._DEFAULT_CHECKS as an instance attribute). This class-level value is
    # only a safe empty fallback so attribute access never raises if the
    # registry hasn't loaded yet. Do NOT add model definitions here -- the
    # single source of truth is dynamic Plugin Factories (app.core.shared_registry).
    _DEFAULT_CHECKS = {}

    def __init__(self, project_base_dir):
        self.project_base_dir = project_base_dir
        self.python_executable = get_python_executable(self.project_base_dir)
        self.cache_path = os.path.join(self.project_base_dir, "temp", "schema_cache.json")
        
        # Ensure directories exist and migrate old root files early
        config_dir = os.path.join(self.project_base_dir, ".config")
        
        # Call migration from RepairMixin
        self._migrate_legacy_file_structures()  # type: ignore
        
        configs_dir = os.path.join(config_dir, "configs")
        models_dir = os.path.join(config_dir, "models")

        self.oldsession_path = os.path.join(configs_dir, "oldsession.yaml")

        # Load configs
        raw_oldsession = self._load_yaml_file(self.oldsession_path)
        
        # Flatten current_settings and job_queue via RepairMixin
        self._flatten_oldsession_structure(raw_oldsession)  # type: ignore
        self.oldsession_config = raw_oldsession
        
        self.system_prompts_path = os.path.join(configs_dir, "system_prompt.yaml")
        self.system_prompts = self._load_yaml_file(self.system_prompts_path)

        # Initialize the LanguageManager
        from app.core.langs.manager import LanguageManager
        self.language_manager = LanguageManager(self.project_base_dir)
        self.localization = self.language_manager.localization

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

        from app.core.desktop.config.studio_ui_map import STUDIO_UI_MAP
        import copy
        self.ui_map = copy.deepcopy(STUDIO_UI_MAP)

        # Resolve and apply language securely
        self.app_language = self.language_manager.resolve_app_language(self.oldsession_config)
        self.ui_map = self.language_manager.apply_language_to_ui_map(self.ui_map, self.app_language)

        # The data is built and stored directly as attributes, not through getter methods
        self.factory_defaults = self._parse_factory_defaults()
        self.full_config_data = self._build_full_config_data()

        # Run the one-time model fallback sweep (once per machine). Repairs any
        # stored profile/default that points at a deleted or not-set-up model.
        # No-op after the first successful run on this machine. Never raises.
        self.optimize_profiles_once()  # type: ignore

    def apply_language(self, lang_id: str):
        """Dynamically switch the active language and re-apply translations to ui_map."""
        self.app_language = lang_id
        from app.core.desktop.config.studio_ui_map import STUDIO_UI_MAP
        import copy
        self.ui_map = copy.deepcopy(STUDIO_UI_MAP)
        self.ui_map = self.language_manager.apply_language_to_ui_map(self.ui_map, self.app_language)

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

    def get_lang_data(self, lang_id: str) -> dict:
        """Proxy method for backward compatibility with UI."""
        return self.language_manager.get_lang_data(lang_id)
