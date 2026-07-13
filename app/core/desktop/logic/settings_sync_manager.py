"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.settings_sync_manager
- RESPONSIBILITY: Synchronize UI widget values with backend configuration data.
- CALLED BY: app.core.desktop.logic.core_handlers.settings_sync
- CALLS TO: PySide6.QtWidgets
- IN = OUT: Reads widget states to save config, or sets widget states from loaded config.
=============================================================================
"""
import os
from typing import Any
from PySide6.QtWidgets import QWidget, QComboBox, QCheckBox, QLineEdit, QButtonGroup, QSlider, QMessageBox
from PySide6.QtCore import Qt, QByteArray
import logging

class SettingsSyncManager:
    def __init__(self, main_window):
        self.mw = main_window

    def connect_widget_signal(self, key: str, widget: QWidget, context_key: str | None = None):
        info = self.mw.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        handler = lambda *args, k=key, ctx=context_key: self.mw._on_setting_changed(k, ctx)

        if isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(handler)
            if key in ['offline_translator', 'ai_translator']:
                widget.currentTextChanged.connect(self.mw._on_translator_changed)
            elif key == 'target_lang':
                widget.currentTextChanged.connect(self.mw._on_target_lang_changed)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(handler)
            if key == 'enable_translator_chain':
                widget.stateChanged.connect(self.mw._update_chain_ui_state)
            if key == 'restore_size_after_colorize':
                widget.stateChanged.connect(self.mw._update_colorize_restore_ui_state)
        elif isinstance(widget, QLineEdit):
            widget.editingFinished.connect(handler)
        elif widget_type == "spinbox":
            from PySide6.QtWidgets import QSpinBox
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(handler)
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                button_group.buttonClicked.connect(handler)
                if key in ['translator_category', 'ai_mode']:
                    button_group.buttonClicked.connect(lambda *args: self.mw._on_translator_category_changed())
                if key == 'ocr_category':
                    button_group.buttonClicked.connect(lambda *args: self.mw._on_ocr_category_changed())
        elif widget_type == "api_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                service = info.get("service", "Translator")
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(lambda text, s=service: self.mw._on_api_profile_changed_generic(text, s))
                le = combo.lineEdit()
                if le:
                    le.returnPressed.connect(combo.showPopup)
        elif widget_type == "pool_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.activated.connect(lambda index: self.mw._on_setting_changed('ai_model'))
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                slider.valueChanged.connect(handler)
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.editingFinished.connect(handler)

    def on_setting_changed(self, key: str, context_key: str | None = None):
        if context_key:
            widget = self.mw.task_widgets[context_key].get(key)
            new_value = self.mw._get_value_from_widget(key, widget)
            if self.mw.task_settings[context_key].get(key) == new_value:
                return
            self.mw.task_settings[context_key][key] = new_value
            logging.info(f"Updated task setting '{context_key}.{key}' to: {new_value}")
            if key in ['translator_category', 'ai_mode', 'api_name']:
                self.mw._update_task_translator_visibility(context_key)
        else:
            widget = self.mw.setting_widgets.get(key)
            if key == 'translator_chain':
                new_value = self.mw._get_translator_chain_string()
            else:
                new_value = self.mw._get_value_from_widget(key, widget)
                
            if isinstance(widget, QComboBox):
                if new_value == "update_trigger":
                    self.mw._trigger_online_config_update_from_combo(key, widget)
                    return

            if self.mw.current_settings.get(key) == new_value:
                return

            self.mw.current_settings[key] = new_value
            logging.info(f"Updated setting '{key}' to: {new_value}")

            if hasattr(self.mw, 'queue_list_widget') and hasattr(self.mw, 'job_queue'):
                selected_items = self.mw.queue_list_widget.selectedItems()
                if selected_items:
                    selected_ids = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}
                    for job in self.mw.job_queue:
                        if job.get('id') in selected_ids:
                            if 'settings' not in job:
                                job['settings'] = {}
                            job['settings'][key] = new_value

            if key in ['ai_translator', 'ai_endpoint', 'ai_model', 'ai_key', 'max_retries', 'api_ocr', 'ocr_api_endpoint', 'ocr_api_model', 'ocr_api_key']:
                is_ocr = key.startswith('ocr_') or key == 'api_ocr'
                p_key = 'ocr_api_name' if is_ocr else 'api_name'
                profile_name = self.mw.current_settings.get(p_key, '').strip()
                
                if profile_name and profile_name.lower() not in ["none", "--- select ---"] and not getattr(self.mw, '_loading_api_profile', False):
                    profiles = self.mw._load_api_profiles()
                    if profile_name in profiles:
                        if key in ['ai_translator', 'api_ocr']:
                            field_name = 'provider'
                        elif is_ocr:
                            field_name = key.replace('ocr_api_', '')
                        else:
                            field_name = key.replace('ai_', '')
                        profiles[profile_name][field_name] = new_value
                        self.mw._save_api_profiles(profiles)
            
            if key in ['translator_category', 'ai_mode', 'ai_translator']:
                self.mw._update_translator_visibility()
                self.mw._update_max_length_label()

            if key in ['system_prompt_profile', 'api_name']:
                self.mw._update_max_length_label()
                
            if key in ['ocr_category', 'ocr_ai_mode', 'api_ocr']:
                self.mw._update_ocr_visibility()
                
            if key in ['inpainter', 'enable_advanced_diffusion', 'diffusion_model']:
                self.mw._update_inpainter_visibility()

            if key == 'app_language':
                self.mw.config_loader.oldsession_config["app_language"] = new_value
                self.mw.config_loader.save_oldsession_config()
                self.mw._rebuild_settings_tab()
                self.mw.update_language_ui()
                # Run language verification specifically for the newly selected language
                if hasattr(self.mw.config_loader, 'language_manager'):
                    self.mw.config_loader.language_manager.run_verification(self.mw.config_loader.ui_map, target_lang=new_value)

    def get_value_from_widget(self, key: str, widget: QWidget) -> Any:
        import app.core.desktop.main_window as mw_module
        if not widget:
            return None

        info = self.mw.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        if isinstance(widget, QComboBox):
            if widget_type == "optionmenu_languages":
                val = widget.currentData()
                if val is not None:
                    return val
                return mw_module.LANGUAGES.get(widget.currentText(), "auto")
            val = widget.currentData()
            
            if val in ["update_trigger", "update_all_software_trigger"]:
                return None
                
            if val is not None:
                return val
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                checked_btn = button_group.checkedButton()
                if checked_btn:
                    internal_id = checked_btn.property("internal_id")
                    value = internal_id if internal_id is not None else checked_btn.text()
                    
                    if key == "upscale_ratio":
                        if value == "Disabled":
                            return None
                        else:
                            return int(value.replace("x", ""))
                    return value
            return None
        elif widget_type in ["api_profile_selector", "ai_model_selector", "combobox_fonts"]:
            combo = widget.findChild(QComboBox) if not isinstance(widget, QComboBox) else widget
            if not combo:
                return None
            if widget_type == "combobox_fonts":
                val = combo.currentData()
                return val if val is not None else combo.currentText()
            return combo.currentText()
        elif widget_type == "open_yaml_button":
            return info.get("default", "Ignored.yaml")
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                precision = 100
                multiplier = info.get("value_multiplier", 1)
                actual_value = (slider.value() / precision) * multiplier
                value_format = info.get("value_format", "{:.0f}")
                if value_format.endswith("0f}"):
                    return int(round(actual_value))
                else:
                    return round(actual_value, 4)
            return None
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                return entry.text()
            return None
        elif widget_type == "spinbox":
            from PySide6.QtWidgets import QSpinBox
            if isinstance(widget, QSpinBox):
                return widget.value()
            return None
        return None

    def set_widget_value(self, key: str, value: Any, widget: QWidget):
        import app.core.desktop.main_window as mw_module
        if not widget or value is None:
            return

        info = self.mw.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        if isinstance(widget, QComboBox):
            if widget_type == "optionmenu_languages":
                index = -1
                for i in range(widget.count()):
                    if widget.itemData(i) == value:
                        index = i
                        break
                if index != -1:
                    widget.setCurrentIndex(index)
                else:
                    display_name = next((k for k, v in mw_module.LANGUAGES.items() if v == value), None)
                    if display_name:
                        widget.setCurrentText(display_name)
            else:
                index = -1
                for i in range(widget.count()):
                    if widget.itemData(i) == value:
                        index = i
                        break
                if index != -1:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentText(str(value))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif widget_type == "segmented_button":
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                value_to_check = str(value)
                if key == "upscale_ratio":
                    if value is None:
                        value_to_check = "Disabled"
                    else:
                        value_to_check = f"{value}x"

                for button in button_group.buttons():
                    internal_id = button.property("internal_id")
                    if (internal_id is not None and str(internal_id) == value_to_check) or button.text() == value_to_check:
                        button.setChecked(True)
                        break
        elif widget_type == "grid_segmented_button":
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                value_to_check = str(value)
                for button in button_group.buttons():
                    internal_id = button.property("internal_id")
                    if (internal_id is not None and str(internal_id) == value_to_check) or button.text() == value_to_check:
                        button.setChecked(True)
                        break
        elif widget_type == "open_yaml_button":
            pass
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider and value is not None:
                precision = 100
                multiplier = info.get("value_multiplier", 1)
                slider_value = int((float(value) / multiplier) * precision) if multiplier != 0 else 0
                slider.setValue(slider_value)

                update_func = getattr(slider, 'update_label_func', None)
                if update_func:
                    update_func(slider_value)
        elif widget_type == "spinbox":
            from PySide6.QtWidgets import QSpinBox
            if isinstance(widget, QSpinBox) and value is not None:
                try:
                    widget.setValue(int(value))
                except (ValueError, TypeError):
                    pass
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.setText(str(value))
        elif widget_type in ["api_profile_selector", "combobox_fonts"]:
            combo = widget.findChild(QComboBox) if not isinstance(widget, QComboBox) else widget
            if combo:
                combo.blockSignals(True)
                if widget_type == "combobox_fonts":
                    idx = combo.findData(str(value))
                    if idx != -1:
                        combo.setCurrentIndex(idx)
                    else:
                        combo.setCurrentText(str(value))
                else:
                    combo.setCurrentText(str(value))
                combo.blockSignals(False)
                
                if widget_type == "combobox_fonts" and hasattr(self.mw, "_style_custom_fonts_in_combobox"):
                    self.mw._style_custom_fonts_in_combobox(combo)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                value_str = str(value)
                if value_str and combo.findText(value_str) == -1:
                    combo.addItem(value_str)
                combo.blockSignals(True)
                combo.setCurrentText(value_str)
                combo.blockSignals(False)

    def load_app_state(self):
        logging.info("Loading previous session state...")
        try:
            settings = getattr(self.mw.config_loader, 'oldsession_config', {})
            geometry_hex = settings.get("window_geometry")
            if geometry_hex:
                self.mw.restoreGeometry(QByteArray.fromHex(geometry_hex.encode('utf-8')))

            self.mw.last_selected_directory = settings.get("last_directory")
            logging.info("Application state loaded.", extra={"ui_level": "SUCCESS"})
        except Exception as e:
            logging.warning(f"[WARNING] Could not load app settings: {e}")

    def save_app_state(self):
        logging.info("Saving application state...")
        if not hasattr(self.mw.config_loader, 'oldsession_config'):
            self.mw.config_loader.oldsession_config = {}
        self.mw.config_loader.oldsession_config["window_geometry"] = self.mw.saveGeometry().toHex().data().decode('utf-8')
        self.mw.config_loader.oldsession_config["last_directory"] = getattr(self.mw, 'last_selected_directory', None)
        
        if hasattr(self.mw.config_loader, 'oldsession_config'):
            if hasattr(self.mw, 'setting_widgets'):
                clean_settings = {}
                for key, widget in self.mw.setting_widgets.items():
                    if key == 'translator_chain':
                        clean_settings[key] = self.mw._get_translator_chain_string()
                    else:
                        val = self.mw._get_value_from_widget(key, widget)
                        if val is not None:
                            clean_settings[key] = val
                self.mw.config_loader.oldsession_config["current_settings"] = clean_settings
                self.mw.current_settings = clean_settings
            else:
                self.mw.config_loader.oldsession_config["current_settings"] = getattr(self.mw, 'current_settings', {})
                
            if hasattr(self.mw, 'theme_combobox'):
                self.mw.config_loader.oldsession_config["theme"] = self.mw.theme_combobox.currentText()
                
            if hasattr(self.mw, 'task_settings') and hasattr(self.mw, 'task_widgets'):
                clean_tasks = {}
                for ctx, ctx_widgets in self.mw.task_widgets.items():
                    clean_tasks[ctx] = {}
                    for key, widget in ctx_widgets.items():
                        val = self.mw._get_value_from_widget(key, widget)
                        if val is not None:
                            clean_tasks[ctx][key] = val
                self.mw.config_loader.oldsession_config["task_settings"] = clean_tasks
                self.mw.task_settings = clean_tasks
            elif hasattr(self.mw, 'task_settings'):
                self.mw.config_loader.oldsession_config["task_settings"] = self.mw.task_settings
            if hasattr(self.mw, 'job_queue'):
                self.mw.config_loader.oldsession_config["job_queue"] = self.mw.job_queue
            if hasattr(self.mw, 'history_queue'):
                self.mw.config_loader.oldsession_config["history_queue"] = self.mw.history_queue
                
            self.mw.config_loader.save_oldsession_config()
            
        logging.info("Application state saved.", extra={"ui_level": "SUCCESS"})
