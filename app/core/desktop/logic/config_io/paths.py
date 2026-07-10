"""
[INTEGRITY NOTES]
Purpose: Manage path resolution for YAML config files.
Responsibilities:
- Provide the absolute path for any given YAML config filename.
"""
import os

def get_yaml_config_path(project_base_dir: str, filename: str) -> str:
    base_dir = os.path.join(project_base_dir, '.config', 'configs')
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)
