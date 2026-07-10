"""
[INTEGRITY NOTES]
Purpose: Clear API configuration UI widgets.
Responsibilities:
- Empty out text inputs and settings related to API endpoints, keys, models.
"""
from ..config.mapping import get_profile_mapping

def clear_api_widgets_generic(main_window, service: str):
    mapping = get_profile_mapping(service)
    for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
        widget = main_window.setting_widgets.get(key)
        if widget:
            main_window.current_settings[key] = ""
            main_window._set_widget_value(key, "", widget)
