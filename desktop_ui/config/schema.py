import os
import json
import re
import subprocess
from typing import Any, Dict

class SchemaMixin:
    def _get_flat_properties(self) -> Dict[str, Any]: return {}
    project_base_dir: str
    cache_path: str
    studio_config: Dict[str, Any]
    backend_schema: Dict[str, Any] | None
    ui_map: Dict[str, Any]
    factory_defaults: Dict[str, Any]
    dict_profiles: Dict[str, Any]


    def _build_full_config_data(self):
        """Builds the final, merged config data for the UI, reading ALL properties."""
        if not self.ui_map:
            return {}
        full_data = {}
        all_properties = self._get_flat_properties()

        # 3. Build the final data structure using the UI map as the guide
        for key, ui_info in self.ui_map.items():
            if key.startswith("__"):
                continue
            merged_info = ui_info.copy()
            merged_info['key'] = key

            # If ui_map has a default, keep it. Otherwise, use factory_defaults
            if 'default' not in merged_info and key in self.factory_defaults:
                merged_info['default'] = self.factory_defaults[key]

            # Add enum values (for dropdowns) if they exist
            prop_def = all_properties.get(key)
            if prop_def and isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)  # type: ignore
                    if enum_def and "enum" in enum_def:
                        custom_choices = self._load_custom_models(key)
                        merged_info['values'] = custom_choices if custom_choices is not None else enum_def["enum"]
            
            # Manually handle UI-only enum settings offline_translator and ai_translator
            if key in ['offline_translator', 'ai_translator']:
                custom_choices = self._load_custom_models(key)
                if custom_choices is not None:
                    merged_info['values'] = custom_choices

            full_data[key] = merged_info

        return full_data

    def _load_custom_models(self, field):
        """Returns the ordered list of model keys for a field.

        Priority: the model registry (single source of truth). The registry
        already populated self._model_checks via load_registry, so we just read
        the ordered keys from it. Falls back to the legacy .config YAML files
        only when the registry has no entry for this field.
        """
        if field == "dict_profile":
            return list(self.dict_profiles.get("profiles", {}).keys())

        registry = getattr(self, "model_registry", {})
        if field in registry and registry[field]:
            return list(registry[field].keys())

        import yaml  # type: ignore
        filename = self._get_yaml_filename(field)  # type: ignore
        model_yaml_path = os.path.join(self.project_base_dir, ".config", filename)
        try:
            if os.path.exists(model_yaml_path):
                with open(model_yaml_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                models_list = []
                if isinstance(content, dict) and "models" in content:
                    models_list = content["models"]
                elif isinstance(content, list):
                    models_list = content
                
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
