import os
import json
import re
from typing import Any

class BaseConfigLoader:
    project_base_dir: str
    cache_path: str
    backend_schema: dict[str, Any] | None
    factory_defaults: dict[str, Any]


    def _save_yaml_file(self, path: str, data: Any) -> None:
        from ruamel.yaml import YAML
        from ruamel.yaml.error import YAMLError
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False  # type: ignore
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
        except (YAMLError, OSError) as e:
            print(f"[ConfigLoader] Error saving {os.path.basename(path)}: {e}")



    def _load_yaml_file(self, path: str) -> dict[str, Any]:
        """Loads a YAML file and returns its content as a dictionary."""
        if os.path.exists(path):
            from ruamel.yaml import YAML
            from ruamel.yaml.error import YAMLError
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False  # type: ignore
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.load(f) or {}
            except (YAMLError, OSError) as e:
                print(f"[ConfigLoader] Error loading YAML file {os.path.basename(path)}: {e}")
        return {}

    def _load_backend_schema(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    print("[ConfigLoader] Loading schema from cache...")
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        fallback_path = os.path.join(self.project_base_dir, ".config", "configs", "schema_fallback.yaml")
        print("[ConfigLoader] Loading static configuration schema from fallback...")
        if os.path.exists(fallback_path):
            try:
                schema_data = self._load_yaml_file(fallback_path)
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

    def _get_flat_properties(self) -> dict[str, Any]:
        """Gathers all root and nested properties from the schema."""
        all_properties = {}
        root_props = self.backend_schema.get("properties", {}) if self.backend_schema else {}
        all_properties.update(root_props)

        for prop in root_props.values():
            ref_path = prop.get("allOf", [{}])[0].get('$ref')
            if ref_path:
                config_def = self._get_definition_from_ref(ref_path)
                if config_def and "properties" in config_def:
                    all_properties.update(config_def["properties"])
        return all_properties

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



    def get_factory_defaults(self):
        return getattr(self, "factory_defaults", {})

    def get_tab_order(self):
        ui_map = getattr(self, "ui_map", {})
        return list(ui_map.keys())
