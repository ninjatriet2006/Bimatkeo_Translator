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
    system_prompts: Dict[str, Any]
    all_model_fields: list[str]


    def _build_full_config_data(self):
        """Builds the final, merged config data for the UI, reading ALL properties."""
        if not self.ui_map:
            return {}
        full_data = {}
        all_properties = self._get_flat_properties()

        # 3. Build the final data structure using the UI map as the guide
        for tab_name, widgets in self.ui_map.items():
            if not isinstance(widgets, dict): continue
            for idx, (key, ui_info) in enumerate(widgets.items()):
                if key.startswith("__"):
                    continue
                merged_info = ui_info.copy()
                merged_info['key'] = key
                merged_info['group'] = tab_name
                merged_info['order'] = idx

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
                
                # Manually handle UI-only enum settings
                if key in self.all_model_fields or key == "system_prompt_profile":
                    custom_choices = self._load_custom_models(key)
                    if custom_choices is not None:
                        merged_info['values'] = custom_choices

                full_data[key] = merged_info

        return full_data

    def _load_custom_models(self, field):
        """Returns the ordered list of model keys for a field.

        Priority: the model registry (single source of truth). The registry
        already populated self._model_checks via load_registry, so we just read
        the ordered keys from it.
        """
        if field == "system_prompt_profile":
            return list(self.system_prompts.get("profiles", {}).keys())

        registry = getattr(self, "model_registry", {})
        if field in registry and registry[field]:
            return list(registry[field].keys())

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
