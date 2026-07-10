"""
[INTEGRITY NOTES]
Purpose: Read API profiles data from storage.
Responsibilities:
- Load data from `api_profiles.yaml`.
- Handle legacy pool migrations.
- Fallback to `.env` variables if necessary.
"""
import os
from .paths import get_api_profiles_file_path

def load_api_profiles(main_window) -> dict:
    path = get_api_profiles_file_path(main_window.project_base_dir)
    if os.path.exists(path):
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.load(f) or {}
            
            # Automigrate pool_profiles.yaml
            pool_path = main_window._get_yaml_config_path('pool_profiles.yaml')
            if os.path.exists(pool_path):
                try:
                    with open(pool_path, 'r', encoding='utf-8') as f:
                        pool_data = yaml.load(f) or {}
                    changed = False
                    for k, v in pool_data.items():
                        if k not in data:
                            data[k] = {"type": "Pool", "service": "Translator", "fallback_list": v}
                            changed = True
                    if changed:
                        main_window._save_yaml_config('api_profiles.yaml', data)
                    os.rename(pool_path, pool_path + ".migrated")
                except Exception as e:
                    print(f"[ERROR] Pool Migration failed: {e}")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load API profiles: {e}")
    
    from dotenv import load_dotenv
    load_dotenv(os.path.join(main_window.project_base_dir, ".env"))

    return {
        "My Custom API": {
            "group": "Standalone",
            "endpoint": "",
            "model": "Auto",
            "key": ""
        }
    }
