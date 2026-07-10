"""
[INTEGRITY NOTES]
Purpose: Handle UI action for saving a new API profile.
Responsibilities:
- Prompt user for a new profile name.
- Read current values from UI widgets.
- Construct new profile and save it to storage.
- Update UI components to reflect the new profile.
"""
from PySide6.QtWidgets import QInputDialog, QComboBox
from ..config.mapping import get_profile_mapping
from ..storage.reader import load_api_profiles
from ..storage.writer import save_api_profiles

def save_api_profile_generic(main_window, service: str):
    mapping = get_profile_mapping(service)
    name_widget = main_window.setting_widgets.get(mapping['name'])
    if not name_widget:
        return
    combo = name_widget.findChild(QComboBox)
    if not combo:
        return
        
    profile_name, ok = QInputDialog.getText(main_window, f"New {service} Profile", "Enter a name for the new API Profile:")
    if not ok:
        return
        
    profile_name = profile_name.strip()
    if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
        if hasattr(main_window, 'app_logger'):
            main_window.app_logger.log("WARNING", "Please enter a valid API Profile Name before saving.")
        return

    endpoint = main_window._get_value_from_widget(mapping['endpoint'], main_window.setting_widgets.get(mapping['endpoint'])) or ''
    provider = main_window._get_value_from_widget(mapping['provider'], main_window.setting_widgets.get(mapping['provider'])) or ''
    model = main_window._get_value_from_widget(mapping['model'], main_window.setting_widgets.get(mapping['model'])) or ''
    key = main_window._get_value_from_widget(mapping['key'], main_window.setting_widgets.get(mapping['key'])) or ''

    profiles = load_api_profiles(main_window)
    profiles[profile_name] = {
        "type": "Standalone",
        "service": service,
        "provider": provider,
        "endpoint": endpoint,
        "model": model,
        "key": key
    }
    save_api_profiles(main_window, profiles)

    filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]
    combo.blockSignals(True)
    combo.clear()
    combo.addItem("--- Select ---")
    combo.addItems(filtered_profiles)
    combo.setCurrentText(profile_name)
    combo.blockSignals(False)
    main_window.current_settings[mapping['name']] = profile_name

    if hasattr(main_window, 'app_logger'):
        main_window.app_logger.log("SUCCESS", f"API Profile '{profile_name}' saved to local config.")
