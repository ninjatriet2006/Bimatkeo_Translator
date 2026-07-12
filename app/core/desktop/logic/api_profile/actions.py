"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.api_profile.actions
- RESPONSIBILITY: Handle UI actions for API profiles (Clear, Save, Change, Delete).
- CALLED BY: app.core.desktop.logic.api_profile.manager
- CALLS TO: app.core.api_profile.storage.*, ..config.mapping
- IN = OUT: Executes action, triggers UI changes.
=============================================================================
"""
from PySide6.QtWidgets import QMessageBox, QComboBox, QInputDialog
from .mapping import get_profile_mapping
from app.core.api.profile.profile_storage import load_api_profiles, save_api_profiles


def clear_api_widgets_generic(main_window, service: str):
    mapping = get_profile_mapping(service)
    for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
        widget = main_window.setting_widgets.get(key)
        if widget:
            main_window.current_settings[key] = ""
            main_window._set_widget_value(key, "", widget)


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


def delete_api_profile_generic(main_window, service: str):
    mapping = get_profile_mapping(service)
    name_widget = main_window.setting_widgets.get(mapping['name'])
    if not name_widget:
        return
    combo = name_widget.findChild(QComboBox)
    if not combo:
        return
    profile_name = combo.currentText().strip()
    if not profile_name or profile_name == "--- Select ---":
        return

    reply = QMessageBox.question(
        main_window,
        "Xác nhận xóa hồ sơ",
        f"Bạn có chắc chắn muốn xóa hồ sơ '{profile_name}' không?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    profiles = load_api_profiles(main_window)
    if profile_name in profiles:
        del profiles[profile_name]
        save_api_profiles(main_window, profiles)

        if hasattr(main_window, 'app_logger'):
            main_window.app_logger.log("SUCCESS", f"Đã xóa hồ sơ '{profile_name}'.")

        filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]

        combo.blockSignals(True)
        combo.clear()
        combo.addItem("--- Select ---")
        combo.addItems(filtered_profiles)
        combo.setCurrentText("--- Select ---")
        combo.blockSignals(False)

        on_api_profile_changed_generic(main_window, "--- Select ---", service)
    else:
        if hasattr(main_window, 'app_logger'):
            main_window.app_logger.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")


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
