"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.profile.profile_storage
- RESPONSIBILITY: Manage file paths, read, and write API profiles data from storage.
- CALLED BY: app.core.desktop.logic.api_profile.manager, app.core.desktop.logic.api_profile.actions
- CALLS TO: None
- IN = OUT: Helper methods for API profile persistence.
=============================================================================
"""
import os

def get_api_profiles_file_path(project_base_dir: str) -> str:
    base_dir = os.path.join(project_base_dir, '.config', 'configs')
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, 'api_profiles.yaml')

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
                    import logging
                    logging.getLogger("APIProfile").error(f"Pool Migration failed: {e}")
            return data
        except Exception as e:
            import logging
            logging.getLogger("APIProfile").error(f"Failed to load API profiles: {e}")
    
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

def save_api_profiles(main_window, profiles: dict):
    main_window._save_yaml_config('api_profiles.yaml', profiles)
