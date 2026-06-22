import os
import json
import re
from typing import Dict, Any, Optional

class BaseConfigLoader:
    project_base_dir: str
    cache_path: str
    studio_config_path: str
    studio_config: Dict[str, Any]
    backend_schema: Optional[Dict[str, Any]]
    ui_map: Dict[str, Any]
    factory_defaults: Dict[str, Any]
    tasks_config: Dict[str, Any]

    def _save_yaml_file(self, path: str, data: Any) -> None:
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False  # type: ignore
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
        except Exception as e:
            print(f"[ConfigLoader] Error saving {os.path.basename(path)}: {e}")

    def save_studio_config(self):
        self._save_yaml_file(self.studio_config_path, self.studio_config)

    def _load_yaml_file(self, path: str) -> Dict[str, Any]:
        """Loads a YAML file and returns its content as a dictionary."""
        if os.path.exists(path):
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False  # type: ignore
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.load(f) or {}
            except Exception as e:
                print(f"[ConfigLoader] Error loading YAML file {os.path.basename(path)}: {e}")
        return {}

    def _load_backend_schema(self):
        if hasattr(self, 'studio_config') and self.studio_config and "schema_cache" in self.studio_config:
            return self.studio_config["schema_cache"]

        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    print("[ConfigLoader] Loading schema from cache...")
                    return json.load(f)
            except Exception:
                pass

        fallback_path = os.path.join(self.project_base_dir, ".config", "configs", "schema_fallback.yaml")
        print("[ConfigLoader] Loading static configuration schema from fallback...")
        if os.path.exists(fallback_path):
            try:
                schema_data = self._load_yaml_file(fallback_path)
                if not hasattr(self, "studio_config"):
                    self.studio_config = {}
                self.studio_config["schema_cache"] = schema_data
                self.save_studio_config()
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
            map_path = os.path.join(self.project_base_dir, '.config', 'configs', 'ui_map.yaml')
            try:
                ui_map = self._load_yaml_file(map_path)
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
        """Loads the special tasks configuration."""
        if hasattr(self, 'studio_config') and self.studio_config and "tasks" in self.studio_config:
            return self.studio_config["tasks"]
        tasks_path = os.path.join(self.project_base_dir, '.config', 'configs', 'tasks.yaml')
        try:
            if not os.path.exists(tasks_path):
                raise FileNotFoundError()
            print("[ConfigLoader] Loading tasks configuration...")
            return self._load_yaml_file(tasks_path)
        except FileNotFoundError:
            print(f"[ERROR] tasks.yaml not found at: {tasks_path}")
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

    def _get_flat_properties(self) -> Dict[str, Any]:
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

    def get_tasks_config(self):
        """Returns the loaded tasks configuration."""
        return getattr(self, "tasks_config", {})

    def get_factory_defaults(self):
        return getattr(self, "factory_defaults", {})

    def get_tab_order(self):
        ui_map = getattr(self, "ui_map", {})
        return ui_map.get("__tab_order__", [])
