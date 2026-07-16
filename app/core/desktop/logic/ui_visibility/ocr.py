"""
[INTEGRITY NOTES]
Purpose: Handle UI visibility toggles for OCR settings.
Responsibilities:
- Determine active OCR category (offline vs ai).
- Toggle visibility of related settings rows and widgets.
"""
def get_active_ocr_category(main_window) -> str:
    widget = main_window.setting_widgets.get('ocr_category')
    if not widget:
        return ''
    val = main_window._get_value_from_widget('ocr_category', widget)
    return val or ''

def update_ocr_visibility(main_window):
    category = get_active_ocr_category(main_window)
    
    show_offline = (category == 'offline')
    show_api = (category == 'api')

    for key in ['offline_detector', 'detection_size', 'offline_ocr']:
        if key in main_window.setting_rows:
            main_window.setting_rows[key].setVisible(show_offline)

    ocr_ai_mode = main_window.current_settings.get('ocr_ai_mode', 'standalone')
    show_standalone = show_api and (ocr_ai_mode == 'standalone')
    show_pool = show_api and (ocr_ai_mode == 'pool')

    if 'ocr_ai_mode' in main_window.setting_rows:
        main_window.setting_rows['ocr_ai_mode'].setVisible(show_api)

    if 'ocr_pool_name' in main_window.setting_rows:
        main_window.setting_rows['ocr_pool_name'].setVisible(show_pool)

    profile_selected = str(main_window.current_settings.get('ocr_api_name', '') or '').strip()
    has_profile = bool(profile_selected and profile_selected.lower() not in ["none", "--- select ---"])

    for key in ['ocr_api_name', 'api_ocr', 'ocr_api_endpoint', 'ocr_api_model', 'ocr_api_key']:
        if key in main_window.setting_rows:
            if key == 'ocr_api_name':
                main_window.setting_rows[key].setVisible(show_standalone)
            else:
                main_window.setting_rows[key].setVisible(show_standalone and has_profile)
                
    from PySide6.QtWidgets import QLineEdit
    provider = main_window._get_value_from_widget('api_ocr', main_window.setting_widgets.get('api_ocr'))
    endpoint_widget = main_window.setting_widgets.get('ocr_api_endpoint')
    if endpoint_widget:
        entry = endpoint_widget if isinstance(endpoint_widget, QLineEdit) else endpoint_widget.findChild(QLineEdit)
        if entry:
            if provider == 'custom_ocr':
                entry.setEnabled(True)
                entry.setReadOnly(False)
            else:
                entry.setEnabled(False)
                entry.setReadOnly(True)
                api_ocr_registry = main_window.config_loader.model_registry.get('api_ocr', {})
                if provider in api_ocr_registry:
                    default_ep = api_ocr_registry[provider].get('default_endpoint', '')
                    if default_ep:
                        entry.setText(default_ep)
                        main_window._on_setting_changed('ocr_api_endpoint')

def on_ocr_category_changed(main_window):
    update_ocr_visibility(main_window)
