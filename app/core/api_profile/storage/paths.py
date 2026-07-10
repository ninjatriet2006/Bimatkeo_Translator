"""
[INTEGRITY NOTES]
Purpose: Manage file paths related to API profiles.
Responsibilities:
- Provide the absolute path for `api_profiles.yaml`.
"""
import os

def get_api_profiles_file_path(project_base_dir: str) -> str:
    base_dir = os.path.join(project_base_dir, '.config', 'configs')
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, 'api_profiles.yaml')
