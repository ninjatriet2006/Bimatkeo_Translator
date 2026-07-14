"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.dynamic_button_router
- RESPONSIBILITY: Route events from dynamic buttons to appropriate managers.
- CALLED BY: app.core.desktop.logic.core_handlers.dynamic_buttons
- CALLS TO: app.core.desktop.logic.fonts.ui_manager, app.core.desktop.logic.offline_models.updater
- IN = OUT: Maps button UI clicks and state updates to backend operations.
=============================================================================
"""
from app.core.desktop.constants import INSTALL_NEW_FONT, UPDATE_ALL_FONTS

class DynamicButtonRouter:
    def __init__(self, main_window, font_ui_manager, model_updater, config_sync):
        self.mw = main_window
        self.font_ui = font_ui_manager
        self.model_updater = model_updater
        self.config_sync = config_sync

    def update_dynamic_btns(self, key: str):
        if not hasattr(self.mw, '_dynamic_btns_map') or key not in self.mw._dynamic_btns_map:
            return
            
        data = self.mw._dynamic_btns_map[key]
        combo = data['combo']
        btn_tick = data['tick']
        btn_download = data['download']
        btn_search = data['search']
        btn_delete = data['delete']
        
        btn_tick.hide()
        btn_download.hide()
        btn_search.hide()
        btn_delete.hide()
        
        current_data = combo.itemData(combo.currentIndex())
        current_text = combo.currentText()
        
        if current_data == "none":
            return
        
        if key == 'font_family':
            if current_text == INSTALL_NEW_FONT:
                btn_tick.show()
                btn_tick.setToolTip("Xác nhận Cài đặt Font mới")
            elif current_text == UPDATE_ALL_FONTS:
                btn_tick.show()
                btn_tick.setToolTip("Xác nhận Cập nhật toàn bộ danh sách Font")
            else:
                installed_fonts = self.font_ui.get_installed_google_fonts()
                if current_text in installed_fonts:
                    btn_download.show()
                    btn_download.setProperty("tooltip_lang_id", "ui_tooltip_download_font")
                    btn_download.setProperty("tooltip_lang_args", [current_text])
                    btn_download.setToolTip(self.mw.get_string("ui_tooltip_download_font").format(current_text))
                else:
                    btn_search.show()
                    btn_search.setProperty("tooltip_lang_id", "ui_tooltip_search_font")
                    btn_search.setProperty("tooltip_lang_args", [current_text])
                    btn_search.setToolTip(self.mw.get_string("ui_tooltip_search_font").format(current_text))
                btn_delete.show()
                btn_delete.setProperty("tooltip_lang_id", "ui_tooltip_delete_font")
                btn_delete.setProperty("tooltip_lang_args", [current_text])
                btn_delete.setToolTip(self.mw.get_string("ui_tooltip_delete_font").format(current_text))
        else:
            if current_data in ["update_all_software_trigger", "update_trigger"]:
                btn_tick.show()
                # Assuming ui_btn_tick_confirm is defined
                btn_tick.setProperty("tooltip_lang_id", "ui_btn_tick_confirm")
                btn_tick.setToolTip(self.mw.get_string("ui_btn_tick_confirm"))
            else:
                btn_download.show()
                btn_download.setProperty("tooltip_lang_id", "ui_tooltip_download_model")
                btn_download.setProperty("tooltip_lang_args", [current_text])
                btn_download.setToolTip(self.mw.get_string("ui_tooltip_download_model").format(current_text))
                btn_delete.show()
                btn_delete.setProperty("tooltip_lang_id", "ui_tooltip_delete_model")
                btn_delete.setProperty("tooltip_lang_args", [current_text])
                btn_delete.setToolTip(self.mw.get_string("ui_tooltip_delete_model").format(current_text))

    def on_dynamic_btn_clicked(self, key: str, action: str):
        if not hasattr(self.mw, '_dynamic_btns_map') or key not in self.mw._dynamic_btns_map:
            return
        combo = self.mw._dynamic_btns_map[key]['combo']
        current_data = combo.itemData(combo.currentIndex())
        current_text = combo.currentText()
        
        if action == 'tick':
            if current_data == "update_all_software_trigger":
                self.model_updater.trigger_all_models_software_update(key)
            elif current_data == "update_trigger":
                if key == "target_lang":
                    self.config_sync.trigger_online_config_update("target_lang")
                elif key in ["offline_translator", "ai_translator"]:
                    self.config_sync.trigger_all_configs_update()
            elif current_text == UPDATE_ALL_FONTS:
                self.font_ui.check_and_update_all_fonts(combo)
            elif current_text == INSTALL_NEW_FONT:
                self.font_ui.prompt_font_install(combo, pre_selected_font=None)
                
        elif action == 'download':
            if key == 'font_family':
                self.font_ui.force_update_current_font(combo)
            else:
                self.model_updater.trigger_model_software_update(key)
                
        elif action == 'search':
            if key == 'font_family':
                if current_text != INSTALL_NEW_FONT:
                    self.font_ui.find_similar_font(combo)
                    
        elif action == 'delete':
            if key == 'font_family':
                self.font_ui.delete_font(current_text)
            else:
                self.model_updater.delete_model_software(key, current_data)
