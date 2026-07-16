"""
[INTEGRITY NOTES]
Purpose: Handle UI visibility toggles for Translator settings.
Responsibilities:
- Determine active translator category (offline vs ai).
- Toggle visibility of related settings rows and widgets.
"""
def get_active_translator_category(main_window) -> str:
    widget = main_window.setting_widgets.get('translator_category')
    if not widget:
        return ''
    val = main_window._get_value_from_widget('translator_category', widget)
    return val or ''

def get_active_translator_name(main_window) -> str:
    category = get_active_translator_category(main_window)
    key = 'offline_translator' if category == 'offline' else 'ai_translator'
    widget = main_window.setting_widgets.get(key)
    if not widget:
        return 'none'
    return main_window._get_value_from_widget(key, widget) or 'none'

def update_translator_visibility(main_window):
    category = get_active_translator_category(main_window)
    
    show_offline = (category == 'offline')
    show_ai = (category == 'api')

    if 'offline_translator' in main_window.setting_rows:
        main_window.setting_rows['offline_translator'].setVisible(show_offline)

    ai_mode = main_window.current_settings.get('ai_mode', 'standalone')
    show_standalone = show_ai and (ai_mode == 'standalone')
    show_pool = show_ai and (ai_mode == 'pool')

    if 'ai_mode' in main_window.setting_rows:
        main_window.setting_rows['ai_mode'].setVisible(show_ai)
        
    if 'pool_name' in main_window.setting_rows:
        main_window.setting_rows['pool_name'].setVisible(show_pool)

    profile_selected = main_window.current_settings.get('api_name', '').strip()
    has_profile = bool(profile_selected and profile_selected.lower() not in ["none", "--- select ---"])
    
    for ai_key in ['api_name', 'ai_translator', 'ai_endpoint', 'ai_model', 'ai_key', 'max_retries']:
        if ai_key in main_window.setting_rows:
            if ai_key == 'api_name':
                main_window.setting_rows[ai_key].setVisible(show_standalone)
            else:
                main_window.setting_rows[ai_key].setVisible(show_standalone and has_profile)

    from PySide6.QtWidgets import QLineEdit
    ai_provider = main_window._get_value_from_widget('ai_translator', main_window.setting_widgets.get('ai_translator'))
    ai_endpoint_widget = main_window.setting_widgets.get('ai_endpoint')
    if ai_endpoint_widget:
        entry = ai_endpoint_widget if isinstance(ai_endpoint_widget, QLineEdit) else ai_endpoint_widget.findChild(QLineEdit)
        if entry:
            if ai_provider == 'custom_openai':
                entry.setEnabled(True)
                entry.setReadOnly(False)
            else:
                entry.setEnabled(False)
                entry.setReadOnly(True)
                ai_registry = getattr(main_window.config_loader, 'model_registry', {}).get('ai_translator', {})
                if ai_provider in ai_registry:
                    default_ep = ai_registry[ai_provider].get('default_endpoint', '')
                    if default_ep:
                        entry.setText(default_ep)
                        main_window._on_setting_changed('ai_endpoint')

def on_translator_category_changed(main_window):
    update_translator_visibility(main_window)
    active_name = get_active_translator_name(main_window)
    main_window._on_translator_changed(active_name)

def update_task_translator_visibility(main_window, context_key: str):
    if not hasattr(main_window, 'task_rows') or context_key not in main_window.task_rows:
        return
    
    settings = main_window.task_settings.get(context_key, {})
    rows = main_window.task_rows.get(context_key, {})
    
    category = settings.get('translator_category', '')
    show_offline = (category == 'offline')
    show_ai = (category == 'api')

    if 'offline_translator' in rows:
        rows['offline_translator'].setVisible(show_offline)

    ai_mode = settings.get('ai_mode', 'standalone')
    show_standalone = show_ai and (ai_mode == 'standalone')
    show_pool = show_ai and (ai_mode == 'pool')

    if 'ai_mode' in rows:
        rows['ai_mode'].setVisible(show_ai)
        
    if 'pool_name' in rows:
        rows['pool_name'].setVisible(show_pool)

    profile_selected = settings.get('api_name', '').strip()
    has_profile = bool(profile_selected and profile_selected.lower() not in ["none", "--- select ---"])
    
    for ai_key in ['api_name', 'ai_translator', 'ai_endpoint', 'ai_model', 'ai_key', 'max_retries']:
        if ai_key in rows:
            if ai_key == 'api_name':
                rows[ai_key].setVisible(show_standalone)
            else:
                rows[ai_key].setVisible(show_standalone and has_profile)
