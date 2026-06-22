import os
import json
import re
import subprocess
from typing import Any, Dict

class SchemaMixin:
    project_base_dir: str
    cache_path: str
    studio_config: Dict[str, Any]
    backend_schema: Dict[str, Any] | None
    ui_map: Dict[str, Any]
    factory_defaults: Dict[str, Any]
    dict_profiles: Dict[str, Any]
    def _load_backend_schema(self):
        # 1. Try loading from studio_config.yaml
        if hasattr(self, 'studio_config') and self.studio_config and "schema_cache" in self.studio_config:
            print("[ConfigLoader] Loading schema from studio_config.yaml...")
            return self.studio_config["schema_cache"]

        # 2. Try loading from static schema cache if exists
        static_path = os.path.join(self.project_base_dir, ".config", "configs", "schema_cache.json")
        if os.path.exists(static_path):
            try:
                with open(static_path, 'r', encoding='utf-8') as f:
                    print("[ConfigLoader] Loading static schema cache...")
                    return json.load(f)
            except Exception:
                pass

        # 3. Try loading from temp cache directory
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    print("[ConfigLoader] Loading schema from cache...")
                    return json.load(f)
            except Exception:
                pass

        fallback_path = os.path.join(self.project_base_dir, ".config", "configs", "schema_fallback.json")
        print("[SchemaLoader] Loading static configuration schema from fallback...")
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                self.studio_config["schema_cache"] = schema_data
                self.save_studio_config()  # type: ignore
                return schema_data
            except Exception as e:
                print(f"[ERROR] Could not load schema fallback: {e}")
                return None
        else:
            print("[ERROR] No schema fallback found!")
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
        if hasattr(self, 'studio_config') and self.studio_config and "ui_map" in self.studio_config:
            ui_map = self.studio_config["ui_map"]
        else:
            map_path = os.path.join(self.project_base_dir, '.config', 'configs', 'ui_map.json')
            try:
                with open(map_path, 'r', encoding='utf-8') as f:
                    ui_map = json.load(f)
            except Exception as e:
                print(f"[ERROR] UI map loading failed: {e}")
                ui_map = {}
                
        # Programmatically override output_format to always use dropdown (optionmenu)
        if isinstance(ui_map, dict) and "output_format" in ui_map:
            if isinstance(ui_map["output_format"], dict):
                ui_map["output_format"]["widget"] = "optionmenu"
                if "options" in ui_map["output_format"]:
                    ui_map["output_format"].pop("options", None)
                    
        return ui_map

    def _load_tasks_config(self):
        """Loads the special tasks configuration from tasks.json."""
        if hasattr(self, 'studio_config') and self.studio_config and "tasks" in self.studio_config:
            return self.studio_config["tasks"]
        tasks_path = os.path.join(self.project_base_dir, '.config', 'configs', 'tasks.json')
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
                if not isinstance(node, dict):
                    return None
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
        root_props = self.backend_schema.get("properties", {}) if self.backend_schema else {}
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

            # If ui_map has a default, keep it. Otherwise, use factory_defaults
            if 'default' not in merged_info and key in self.factory_defaults:
                merged_info['default'] = self.factory_defaults[key]

            # Add enum values (for dropdowns) if they exist
            prop_def = all_properties.get(key)
            if prop_def and isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)
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
