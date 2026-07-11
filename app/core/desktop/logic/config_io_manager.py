"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.config_io_manager
- RESPONSIBILITY: Manage path resolution and saving logic for YAML config files.
- CALLED BY: app.core.desktop.logic.core_handlers.config_io
- CALLS TO: ruamel.yaml
- IN = OUT: Reads and writes generic configuration data to disk.
=============================================================================
"""
import os
from ruamel.yaml import YAML

def get_yaml_config_path(project_base_dir: str, filename: str) -> str:
    base_dir = os.path.join(project_base_dir, '.config', 'configs')
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)

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
