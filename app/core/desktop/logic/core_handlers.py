from PySide6.QtWidgets import QWidget, QComboBox

class HandlersMixin:
    # Phase 1: AI Models & API Profiles & UI Visibility
    @property
    def _api_profile_mgr(self):
        if not hasattr(self, '__api_profile_mgr'):
            from app.core.desktop.logic.api_profile.manager import ApiProfileManager
            self.__api_profile_mgr = ApiProfileManager(self)
        return self.__api_profile_mgr

    def _get_active_translator_category(self) -> str:
        from app.core.desktop.logic.ui_visibility.translator import get_active_translator_category
        return get_active_translator_category(self)

    def _get_active_translator_name(self) -> str:
        from app.core.desktop.logic.ui_visibility.translator import get_active_translator_name
        return get_active_translator_name(self)

    def _update_translator_visibility(self):
        from app.core.desktop.logic.ui_visibility.translator import update_translator_visibility
        update_translator_visibility(self)

    def _get_active_ocr_category(self) -> str:
        from app.core.desktop.logic.ui_visibility.ocr import get_active_ocr_category
        return get_active_ocr_category(self)

    def _update_ocr_visibility(self):
        from app.core.desktop.logic.ui_visibility.ocr import update_ocr_visibility
        update_ocr_visibility(self)

    def _update_inpainter_visibility(self):
        from app.core.desktop.logic.ui_visibility.inpainter import update_inpainter_visibility
        update_inpainter_visibility(self)

    def _on_ocr_category_changed(self):
        from app.core.desktop.logic.ui_visibility.ocr import on_ocr_category_changed
        on_ocr_category_changed(self)

    def _update_task_translator_visibility(self, context_key: str):
        from app.core.desktop.logic.ui_visibility.translator import update_task_translator_visibility
        update_task_translator_visibility(self, context_key)

    def _on_translator_category_changed(self):
        from app.core.desktop.logic.ui_visibility.translator import on_translator_category_changed
        on_translator_category_changed(self)

    def _fetch_ai_models(self, button):
        from app.core.desktop.logic.ai_models.fetcher import fetch_ai_models
        fetch_ai_models(self, button)

    def _show_fetched_models(self, models, button):
        from app.core.desktop.logic.ai_models.fetcher import show_fetched_models
        show_fetched_models(self, models, button)

    def _select_fetched_model(self, model_name, entry_widget):
        from app.core.desktop.logic.ai_models.fetcher import select_fetched_model
        select_fetched_model(self, model_name, entry_widget)

    def _on_models_fetched(self, models, button):
        self._show_fetched_models(models, button)

    def _test_ai_model(self, button, combo):
        from app.core.desktop.logic.ai_models.tester import test_ai_model
        test_ai_model(self, button, combo)

    def _on_test_finished(self, success, message, button):
        from app.core.desktop.logic.ai_models.tester import on_test_finished
        on_test_finished(self, success, message, button)

    def _on_fetch_finished(self, button):
        from app.core.desktop.logic.ai_models.fetcher import on_fetch_finished
        on_fetch_finished(self, button)

    def _get_api_profiles_file_path(self) -> str:
        return self._api_profile_mgr.get_api_profiles_file_path()

    def _load_api_profiles(self) -> dict:
        return self._api_profile_mgr.load_api_profiles()

    def _get_yaml_config_path(self, filename: str) -> str:
        from app.core.desktop.logic.config_io.paths import get_yaml_config_path
        return get_yaml_config_path(self.project_base_dir, filename)

    def _save_yaml_config(self, filename: str, data: dict, wrap_key: str = None):
        from app.core.desktop.logic.config_io.yaml_io import save_yaml_config
        save_yaml_config(self.project_base_dir, filename, data, wrap_key)

    def _save_api_profiles(self, profiles: dict):
        self._api_profile_mgr.save_api_profiles(profiles)

    def _get_profile_mapping(self, service: str) -> dict:
        return self._api_profile_mgr.get_profile_mapping(service)

    def _save_api_profile_generic(self, service: str):
        self._api_profile_mgr.save_api_profile_generic(service)

    def _delete_api_profile_generic(self, service: str):
        self._api_profile_mgr.delete_api_profile_generic(service)

    def _clear_api_widgets_generic(self, service: str):
        self._api_profile_mgr.clear_api_widgets_generic(service)

    def _on_api_profile_changed_generic(self, profile_name: str, service: str):
        self._api_profile_mgr.on_api_profile_changed_generic(profile_name, service)

    def _get_pool_profiles_file_path(self) -> str:
        return self._get_yaml_config_path('pool_profiles.yaml')

    def _load_pool_profiles(self, service: str = "Translator") -> dict:
        profiles = self._load_api_profiles()
        return {k: v.get("fallback_list", []) for k, v in profiles.items() if v.get("type") == "Pool" and v.get("service", "Translator") == service}

    def _save_pool_profiles(self, pools: dict, service: str = "Translator"):
        profiles = self._load_api_profiles()
        profiles = {k: v for k, v in profiles.items() if not (v.get("type") == "Pool" and v.get("service", "Translator") == service)}
        for k, v in pools.items():
            profiles[k] = {"type": "Pool", "service": service, "fallback_list": v}
        self._save_api_profiles(profiles)

    def _open_manage_pools_dialog(self, service: str = "Translator"):
        from app.core.desktop.ui.dialogs.manage_pools_dialog import ManagePoolsDialog
        dialog = ManagePoolsDialog(self, service)
        dialog.exec()

    # Phase 2: Fonts, Models, Config, Dynamic Buttons
    @property
    def font_ui_manager(self):
        if not hasattr(self, '_font_ui_manager_obj'):
            from app.core.desktop.logic.fonts.ui_manager import FontUIManager
            self._font_ui_manager_obj = FontUIManager(self)
        return self._font_ui_manager_obj

    @property
    def model_software_updater(self):
        if not hasattr(self, '_model_software_updater_obj'):
            from app.core.desktop.logic.models.updater import ModelSoftwareUpdater
            self._model_software_updater_obj = ModelSoftwareUpdater(self)
        return self._model_software_updater_obj

    @property
    def config_sync_manager(self):
        if not hasattr(self, '_config_sync_manager_obj'):
            from app.core.desktop.logic.config_sync.manager import ConfigSyncManager
            self._config_sync_manager_obj = ConfigSyncManager(self)
        return self._config_sync_manager_obj

    @property
    def dynamic_button_router(self):
        if not hasattr(self, '_dynamic_button_router_obj'):
            from app.core.desktop.logic.dynamic_buttons.router import DynamicButtonRouter
            self._dynamic_button_router_obj = DynamicButtonRouter(
                self, 
                self.font_ui_manager, 
                self.model_software_updater, 
                self.config_sync_manager
            )
        return self._dynamic_button_router_obj

    def _get_fonts_manager(self):
        return self.font_ui_manager.get_fonts_manager()

    def _build_font_map(self):
        return self.font_ui_manager.build_font_map()

    def _get_google_font_family_from_filename(self, filename: str) -> str:
        return self.font_ui_manager.get_google_font_family_from_filename(filename)

    def _get_installed_google_fonts(self) -> dict:
        return self.font_ui_manager.get_installed_google_fonts()

    def _save_font_version_from_online_metadata(self, font_family: str):
        return self.font_ui_manager.save_font_version_from_online_metadata(font_family)

    def _force_update_current_font(self, main_font_combo):
        return self.font_ui_manager.force_update_current_font(main_font_combo)

    def _prompt_font_install(self, main_font_combo, pre_selected_font=None):
        return self.font_ui_manager.prompt_font_install(main_font_combo, pre_selected_font)

    def _find_similar_font(self, main_font_combo):
        return self.font_ui_manager.find_similar_font(main_font_combo)

    def _check_and_update_all_fonts(self, main_font_combo):
        return self.font_ui_manager.check_and_update_all_fonts(main_font_combo)

    def _download_updates(self, updates, main_font_combo):
        return self.font_ui_manager.download_updates(updates, main_font_combo)

    def _update_dynamic_btns(self, key: str):
        return self.dynamic_button_router.update_dynamic_btns(key)

    def _on_dynamic_btn_clicked(self, key: str, action: str):
        return self.dynamic_button_router.on_dynamic_btn_clicked(key, action)

    def _delete_font(self, font_name: str):
        return self.font_ui_manager.delete_font(font_name)

    def _delete_model_software(self, key: str, model_name: str):
        return self.model_software_updater.delete_model_software(key, model_name)

    def _trigger_all_models_software_update(self, key: str):
        return self.model_software_updater.trigger_all_models_software_update(key)

    def _trigger_model_software_update(self, key: str):
        return self.model_software_updater.trigger_model_software_update(key)

    def _trigger_online_config_update_from_combo(self, key: str, combo):
        pass

    def _trigger_online_config_update(self, key: str):
        return self.config_sync_manager.trigger_online_config_update(key)

    def _trigger_all_configs_update(self):
        return self.config_sync_manager.trigger_all_configs_update()

    def _handle_config_update_finished(self, success, message):
        return self.config_sync_manager.handle_config_update_finished(success, message)

    def _reload_dynamic_configurations(self):
        return self.config_sync_manager.reload_dynamic_configurations()

    # Phase 3: Settings Sync, UI Dropdowns, Job Queue, Export, Themes
    @property
    def settings_sync_manager(self):
        if not hasattr(self, '_settings_sync_manager_obj'):
            from app.core.desktop.logic.settings.sync import SettingsSyncManager
            self._settings_sync_manager_obj = SettingsSyncManager(self)
        return self._settings_sync_manager_obj

    @property
    def ui_dropdown_manager(self):
        if not hasattr(self, '_ui_dropdown_manager_obj'):
            from app.core.desktop.logic.ui_updates.dropdowns import UIDropdownManager
            self._ui_dropdown_manager_obj = UIDropdownManager(self)
        return self._ui_dropdown_manager_obj

    @property
    def job_queue_ui_manager(self):
        if not hasattr(self, '_job_queue_ui_manager_obj'):
            from app.core.desktop.logic.job_queue.ui_manager import JobQueueUIManager
            self._job_queue_ui_manager_obj = JobQueueUIManager(self)
        return self._job_queue_ui_manager_obj

    @property
    def export_manager(self):
        if not hasattr(self, '_export_manager_obj'):
            from app.core.desktop.logic.export.manager import ExportManager
            self._export_manager_obj = ExportManager(self)
        return self._export_manager_obj

    @property
    def theme_manager(self):
        if not hasattr(self, '_theme_manager_obj'):
            from app.core.desktop.logic.themes.manager import ThemeManager
            self._theme_manager_obj = ThemeManager(self)
        return self._theme_manager_obj

    def _on_font_scale_changed(self, text: str):
        current_theme_name = self.theme_combobox.currentText()
        self._apply_theme(current_theme_name)

    def _connect_widget_signal(self, key: str, widget: QWidget, context_key: str = None):
        return self.settings_sync_manager.connect_widget_signal(key, widget, context_key)

    def _on_setting_changed(self, key: str, context_key: str = None):
        return self.settings_sync_manager.on_setting_changed(key, context_key)

    def _update_max_length_label(self):
        return self.ui_dropdown_manager.update_max_length_label()

    def _on_translator_changed(self, translator_name: str):
        return self.ui_dropdown_manager.on_translator_changed(translator_name)

    def _is_translator_supported_for_target(self, translator_name: str, target_code: str) -> bool:
        return self.ui_dropdown_manager.is_translator_supported_for_target(translator_name, target_code)

    def _filter_translator_dropdowns(self, target_lang_name: str, context_key: str = None):
        return self.ui_dropdown_manager.filter_translator_dropdowns(target_lang_name, context_key)

    def _filter_chain_step_translator_dropdown(self, target_lang_name: str, translator_combo: QComboBox):
        return self.ui_dropdown_manager.filter_chain_step_translator_dropdown(target_lang_name, translator_combo)

    def _on_target_lang_changed(self, target_lang_name: str):
        return self.ui_dropdown_manager.on_target_lang_changed(target_lang_name)

    def _filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        return self.ui_dropdown_manager.filter_language_dropdown(translator_name, lang_combo)

    def _get_value_from_widget(self, key: str, widget: QWidget) -> any:
        return self.settings_sync_manager.get_value_from_widget(key, widget)

    def _set_widget_value(self, key: str, value: any, widget: QWidget):
        return self.settings_sync_manager.set_widget_value(key, value, widget)

    def closeEvent(self, event):
        from PySide6.QtWidgets import QMessageBox
        if getattr(self, 'is_running_pipeline', False):
            reply = QMessageBox.question(self, "Confirm Exit",
                                         "A process is still running. Are you sure you want to stop it and exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._stop_pipeline()
            else:
                event.ignore()
                return

        self._save_app_state()
        event.accept()

    def _load_app_state(self):
        return self.settings_sync_manager.load_app_state()

    def _save_app_state(self):
        return self.settings_sync_manager.save_app_state()

    def _load_themes(self):
        return self.theme_manager.load_themes()

    def _apply_theme(self, theme_name: str):
        return self.theme_manager.apply_theme(theme_name)

    def _show_queue_context_menu(self, position):
        return self.job_queue_ui_manager.show_queue_context_menu(position)

    def _resume_selected_jobs(self):
        return self.job_queue_ui_manager.resume_selected_jobs()

    def _restart_selected_jobs(self):
        return self.job_queue_ui_manager.restart_selected_jobs()

    def _show_history_context_menu(self, position):
        return self.job_queue_ui_manager.show_history_context_menu(position)

    def _export_detector_image(self):
        return self.export_manager.export_detector_image()

    def _export_ocr_data(self):
        return self.export_manager.export_ocr_data()

    def _export_translator_data(self):
        return self.export_manager.export_translator_data()

    def _export_inpainter_image(self):
        return self.export_manager.export_inpainter_image()

    def _export_render_image(self):
        return self.export_manager.export_render_image()
