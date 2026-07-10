"""
[INTEGRITY NOTES]
Purpose: Handle UI action when the selected API profile changes.
Responsibilities:
- Load selected profile data.
- Update UI widgets to match profile data.
- Trigger visibility updates.
"""
from ..config.mapping import get_profile_mapping
from app.core.api_profile.storage.reader import load_api_profiles
from .clear_action import clear_api_widgets_generic

def on_api_profile_changed_generic(main_window, profile_name: str, service: str):
    profile_name = (profile_name or "").strip()
    mapping = get_profile_mapping(service)
    
    if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
        main_window.current_settings[mapping['name']] = ""
        clear_api_widgets_generic(main_window, service)
        update_method = getattr(main_window, f"_update_{service.lower()}_visibility", None)
        if update_method: update_method()
        return
        
    profiles = load_api_profiles(main_window)
    if profile_name in profiles:
        profile = profiles[profile_name]
        
        main_window._loading_api_profile = True
        try:
            for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
                widget = main_window.setting_widgets.get(key)
                if widget:
                    val = profile.get(field, '')
                    main_window.current_settings[key] = val
                    main_window._set_widget_value(key, val, widget)
        finally:
            main_window._loading_api_profile = False
    else:
        main_window.current_settings[mapping['name']] = profile_name
        clear_api_widgets_generic(main_window, service)
        
    update_method = getattr(main_window, f"_update_{service.lower()}_visibility", None)
    if update_method: update_method()
