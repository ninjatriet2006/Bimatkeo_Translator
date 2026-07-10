"""
[INTEGRITY NOTES]
Purpose: Save API profiles data to storage.
Responsibilities:
- Save dictionary data into `api_profiles.yaml`.
"""

def save_api_profiles(main_window, profiles: dict):
    main_window._save_yaml_config('api_profiles.yaml', profiles)
