"""
[INTEGRITY NOTES]
Purpose: Handle saving YAML config files.
Responsibilities:
- Provide a robust way to save data to a YAML file with consistent formatting.
"""
from ruamel.yaml import YAML
from .paths import get_yaml_config_path

def save_yaml_config(project_base_dir: str, filename: str, data: dict, wrap_key: str = None):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    path = get_yaml_config_path(project_base_dir, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            if wrap_key:
                yaml.dump({wrap_key: data}, f)
            else:
                yaml.dump(data, f)
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")
