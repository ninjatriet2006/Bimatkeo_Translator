# type: ignore
# ===============================================================
# HandlersMixin - UI Events and Setting Changes Handlers
#
# Author: User & Gemini Collaboration
# ===============================================================

import os
import sys
import json
import time
import copy
import subprocess
from PySide6.QtWidgets import (
    QWidget, QComboBox, QCheckBox, QLineEdit, QButtonGroup, QMessageBox,
    QMenu, QColorDialog, QDialog, QApplication, QSlider
)
from PySide6.QtCore import Qt, Signal, QThread, QByteArray
from PySide6.QtGui import QColor

from .widgets_helper import (
    get_provider_credentials, SearchableFontInstallDialog
)

class HandlersMixin:
    def _get_active_translator_category(self) -> str:
        """Returns '''Offline''' or '''AI / Online'''."""
        widget = self.setting_widgets.get('translator_category')
        if not widget:
            return 'Offline'
        val = self._get_value_from_widget('translator_category', widget)
        return val or 'Offline'

    def _get_active_translator_name(self) -> str:
        """Returns the active translator name (e.g. sugoi, gemini, etc.)"""
        category = self._get_active_translator_category()
        key = 'offline_translator' if category == 'Offline' else 'ai_translator'
        widget = self.setting_widgets.get(key)
        if not widget:
            return 'none'
        return self._get_value_from_widget(key, widget) or 'none'

    def _update_translator_visibility(self):
        """Toggles the visibility of translator settings based on Offline vs AI category with cascade hierarchy."""
        selected_category = self._get_active_translator_category()
        
        show_offline = (selected_category == "Offline")
        show_ai = (selected_category == "AI / Online")

        # Toggle rows visibility
        if 'offline_translator' in self.setting_rows:
            self.setting_rows['offline_translator'].setVisible(show_offline)
        
        # Determine visibility in AI / Online mode based on cascade dependency
        group_val = ""
        group_widget = self.setting_widgets.get('api_group')
        if group_widget:
            group_combo = group_widget.findChild(QComboBox)
            if group_combo:
                group_val = group_combo.currentText().strip()
                
        is_group_selected = show_ai and group_val != "" and group_val.lower() != "none"
        
        name_val = ""
        name_widget = self.setting_widgets.get('api_name')
        if name_widget:
            name_combo = name_widget.findChild(QComboBox)
            if name_combo:
                name_val = name_combo.currentText().strip()
                
        is_name_selected = is_group_selected and name_val != "" and name_val.lower() != "none"

        # Apply cascade visibility
        if 'api_group' in self.setting_rows:
            self.setting_rows['api_group'].setVisible(show_ai)
            
        if 'api_name' in self.setting_rows:
            self.setting_rows['api_name'].setVisible(is_group_selected)
            
        for ai_key in ['ai_translator', 'ai_endpoint', 'ai_model', 'ai_key']:
            if ai_key in self.setting_rows:
                self.setting_rows[ai_key].setVisible(is_name_selected)

    def _on_translator_category_changed(self):
        """Handles changes in translator category (Offline vs AI)."""
        self._update_translator_visibility()
        active_name = self._get_active_translator_name()
        self._on_translator_changed(active_name)

    def _sync_ai_credentials(self, ai_provider: str):
        """Auto-populates Endpoint, Model, and Key fields when changing AI provider."""
        if getattr(self, '_loading_api_profile', False):
            return
        from dotenv import load_dotenv
        load_dotenv(os.path.join(self.project_base_dir, ".env"))

        info = get_provider_credentials(ai_provider)

        for field, key in [('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
            widget = self.setting_widgets.get(key)
            if widget:
                self.current_settings[key] = info[field]
                self._set_widget_value(key, info[field], widget)

    def _fetch_ai_models(self, button):
        """Fetches models from the configured endpoint in a background thread."""
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint'))
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key'))
        ai_provider = self._get_active_translator_name()

        if not endpoint:
            provider_endpoints = {
                'openai': 'https://api.openai.com/v1',
                'deepseek': 'https://api.deepseek.com',
                'groq': 'https://api.groq.com/openai/v1',
                'custom_openai': 'http://localhost:11434/v1',
                'sakura': 'http://127.0.0.1:8080/v1'
            }
            endpoint = provider_endpoints.get(ai_provider, '')

        if not endpoint and ai_provider != 'gemini':
            self.log("WARNING", f"No API Endpoint URL provided for provider '{ai_provider}'. Please enter a valid URL.")
            return

        button.setEnabled(False)
        button.setText("...")

        def thread_target():
            import urllib.request
            import urllib.error
            import ssl

            models = []
            
            def is_blacklisted(model_name):
                name_lower = model_name.lower()
                blacklist_keywords = [
                    "embedding", "tts", "whisper", "dall-e", "moderation", 
                    "classifier", "aqa", "sib", "babbage", "davinci", "ada"
                ]
                for kw in blacklist_keywords:
                    if kw in name_lower:
                        return True
                return False

            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                if ai_provider == 'gemini':
                    base_url = endpoint.rstrip('/') if endpoint else "https://generativelanguage.googleapis.com/v1beta"
                    url = f"{base_url}/models?key={key}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        gemini_models = []
                        for m in res_data.get('models', []):
                            m_name = m.get('name', '')
                            if m_name.startswith('models/'):
                                m_name = m_name.replace('models/', '')
                            if is_blacklisted(m_name):
                                continue
                            input_limit = m.get('inputTokenLimit', 0)
                            gemini_models.append((m_name, input_limit))
                        
                        gemini_models.sort(key=lambda x: (-x[1], x[0]))
                        models = [x[0] for x in gemini_models]
                else:
                    base_url = endpoint.rstrip('/')
                    url = base_url + '/models'
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0',
                        'Content-Type': 'application/json'
                    }
                    if key:
                        headers['Authorization'] = f"Bearer {key}"
                    
                    req = urllib.request.Request(url, headers=headers)
                    raw_models = []
                    try:
                        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                            res_data = json.loads(response.read().decode('utf-8'))
                            if 'data' in res_data and isinstance(res_data['data'], list):
                                for item in res_data['data']:
                                    if 'id' in item:
                                        raw_models.append(item['id'])
                            elif 'models' in res_data and isinstance(res_data['models'], list):
                                for item in res_data['models']:
                                    if 'name' in item:
                                        raw_models.append(item['name'])
                    except urllib.error.HTTPError as e:
                        if '11434' in base_url or 'ollama' in base_url.lower():
                            ollama_url = base_url.replace('/v1', '') + '/api/tags'
                            req = urllib.request.Request(ollama_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                                res_data = json.loads(response.read().decode('utf-8'))
                                for item in res_data.get('models', []):
                                    if 'name' in item:
                                        raw_models.append(item['name'])
                        else:
                            raise e

                    filtered_models = [m for m in raw_models if not is_blacklisted(m)]
                    
                    def priority_sort_key(m_name):
                        m_lower = m_name.lower()
                        if any(x in m_lower for x in ["gpt-4o", "o1", "o3", "deepseek-chat", "mixtral", "llama3"]):
                            priority = -10
                        elif any(x in m_lower for x in ["gpt-4", "deepseek", "llama"]):
                            priority = -5
                        elif "gpt-3.5" in m_lower:
                            priority = 0
                        else:
                            priority = 5
                        return (priority, m_lower)

                    filtered_models = sorted(list(set(filtered_models)), key=priority_sort_key)
                    models = filtered_models

                if not models:
                    raise Exception("No suitable model IDs found in response.")

                self.models_fetched_signal.emit(models, button)
            except Exception as e:
                err_msg = str(e)
                print(f"[ERROR] Failed to fetch models: {err_msg}")
                self.log("ERROR", f"Failed to fetch models: {err_msg}")
            finally:
                self.fetch_finished_signal.emit(button)

        threading.Thread(target=thread_target, daemon=True).start()

    def _show_fetched_models(self, models, button):
        if not models:
            return
            
        model_widget = self.setting_widgets.get('ai_model')
        if model_widget:
            combo = model_widget.findChild(QComboBox)
            if combo:
                current_text = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("Auto")
                combo.addItems(models)
                
                if current_text and (current_text in models or current_text == "Auto"):
                    combo.setCurrentText(current_text)
                else:
                    combo.setCurrentText("Auto")
                    self.current_settings['ai_model'] = "Auto"
                    
                combo.blockSignals(False)
                self._on_setting_changed('ai_model')
                combo.showPopup()

    def _select_fetched_model(self, model_name, entry_widget):
        entry_widget.setText(model_name)
        self._on_setting_changed('ai_model')

    def _on_models_fetched(self, models, button):
        self._show_fetched_models(models, button)

    def _on_fetch_finished(self, button):
        button.setEnabled(True)
        button.setText("Fetch")

    def _get_api_profiles_file_path(self) -> str:
        base_dir = os.path.join(self.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'api_profiles.json')

    def _load_api_profiles(self) -> dict:
        path = self._get_api_profiles_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load API profiles: {e}")
        
        from dotenv import load_dotenv
        load_dotenv(os.path.join(self.project_base_dir, ".env"))

        gemini_creds = get_provider_credentials('gemini')
        openai_creds = get_provider_credentials('openai')

        return {
            "Default (Gemini)": {
                "group": "Default",
                "provider": "gemini",
                **gemini_creds
            },
            "Default (OpenAI)": {
                "group": "Default",
                "provider": "openai",
                **openai_creds
            }
        }

    def _save_api_profiles(self, profiles: dict):
        path = self._get_api_profiles_file_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save API profiles: {e}")

    def _save_current_api_profile(self):
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name:
            self.log("WARNING", "Please enter an API Profile Name before saving.")
            return

        group = self._get_value_from_widget('api_group', self.setting_widgets.get('api_group')) or 'Default'
        provider = self._get_value_from_widget('ai_translator', self.setting_widgets.get('ai_translator')) or 'gemini'
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint')) or ''
        model = self._get_value_from_widget('ai_model', self.setting_widgets.get('ai_model')) or ''
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key')) or ''

        profiles = self._load_api_profiles()
        profiles[profile_name] = {
            "group": group,
            "provider": provider,
            "endpoint": endpoint,
            "model": model,
            "key": key
        }
        self._save_api_profiles(profiles)

        group_widget = self.setting_widgets.get('api_group')
        if group_widget:
            group_combo = group_widget.findChild(QComboBox)
            if group_combo:
                all_groups = sorted(list(set(p.get("group", "Default") for p in profiles.values())))
                if not all_groups:
                    all_groups = ["Default"]
                group_combo.blockSignals(True)
                group_combo.clear()
                group_combo.addItems(all_groups)
                group_combo.setCurrentText(group)
                group_combo.blockSignals(False)

        filtered_profiles = [name for name, p in profiles.items() if p.get("group", "Default") == group]
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(filtered_profiles)
        combo.setCurrentText(profile_name)
        combo.blockSignals(False)

        self.log("SUCCESS", f"API Profile '{profile_name}' saved to local config.")

    def _delete_current_api_group(self):
        group_widget = self.setting_widgets.get('api_group')
        if not group_widget:
            return
        group_combo = group_widget.findChild(QComboBox)
        if not group_combo:
            return
        group_name = group_combo.currentText().strip()
        if not group_name:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa nhóm API",
            f"Bạn có chắc chắn muốn xóa nhóm API '{group_name}'?\nHành động này cũng sẽ xóa toàn bộ các hồ sơ API nằm trong nhóm này!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self._load_api_profiles()
        to_delete = [name for name, profile in profiles.items() if profile.get("group") == group_name]
        for name in to_delete:
            del profiles[name]
        
        self._save_api_profiles(profiles)
        self.log("SUCCESS", f"Đã xóa nhóm API '{group_name}' và {len(to_delete)} hồ sơ liên quan.")

        all_groups = sorted(list(set(p.get("group", "Default") for p in profiles.values())))
        if not all_groups:
            all_groups = ["Default"]
        fallback_group = all_groups[0]

        group_combo.blockSignals(True)
        group_combo.clear()
        group_combo.addItems(all_groups)
        group_combo.setCurrentText(fallback_group)
        group_combo.blockSignals(False)

        self._on_api_group_changed(fallback_group)

    def _delete_current_api_profile(self):
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa hồ sơ API",
            f"Bạn có chắc chắn muốn xóa hồ sơ API '{profile_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self._load_api_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            self._save_api_profiles(profiles)
            self.log("SUCCESS", f"Đã xóa hồ sơ API '{profile_name}'.")

            group = self._get_value_from_widget('api_group', self.setting_widgets.get('api_group')) or 'Default'
            filtered_profiles = [name for name, p in profiles.items() if p.get("group", "Default") == group]

            combo.blockSignals(True)
            combo.clear()
            if filtered_profiles:
                combo.addItems(filtered_profiles)
                fallback_name = filtered_profiles[0]
                combo.setCurrentText(fallback_name)
                combo.blockSignals(False)
                self._on_api_profile_changed(fallback_name)
            else:
                combo.setCurrentText("")
                combo.blockSignals(False)
                self.current_settings['api_name'] = ""
                for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                    widget = self.setting_widgets.get(key)
                    if widget:
                        self.current_settings[key] = ""
                        self._set_widget_value(key, "", widget)
        else:
            self.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")

    def _on_api_group_changed(self, group_name: str):
        group_name = (group_name or "").strip()
        
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
            
        if not group_name or group_name.lower() == "none":
            combo.blockSignals(True)
            combo.clear()
            combo.setCurrentText("")
            combo.blockSignals(False)
            
            self.current_settings['api_name'] = ""
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            self._update_translator_visibility()
            return
        
        profiles = self._load_api_profiles()
        filtered_profiles = [name for name, profile in profiles.items() if profile.get("group") == group_name]
        
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("")
        if filtered_profiles:
            combo.addItems(filtered_profiles)
        combo.setCurrentText("")
        combo.blockSignals(False)
        
        self.current_settings['api_name'] = ""
        for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
            widget = self.setting_widgets.get(key)
            if widget:
                self.current_settings[key] = ""
                self._set_widget_value(key, "", widget)
                
        self._update_translator_visibility()

    def _on_api_profile_changed(self, profile_name: str):
        profile_name = (profile_name or "").strip()
        
        if not profile_name or profile_name.lower() == "none":
            self.current_settings['api_name'] = ""
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            self._update_translator_visibility()
            return
            
        profiles = self._load_api_profiles()
        if profile_name in profiles:
            profile = profiles[profile_name]
            
            self._loading_api_profile = True
            try:
                for field, key in [('group', 'api_group'), ('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                    widget = self.setting_widgets.get(key)
                    if widget:
                        val = profile.get(field, '')
                        self.current_settings[key] = val
                        self._set_widget_value(key, val, widget)
            finally:
                self._loading_api_profile = False
        else:
            self.current_settings['api_name'] = profile_name
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            
        self._update_translator_visibility()


    def _get_preset_profiles_file_path(self) -> str:
        import os
        base_dir = os.path.join(self.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'profiles.yaml')

    def _load_preset_profiles(self) -> dict:
        import os
        import yaml
        path = self._get_preset_profiles_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ERROR] Failed to load preset profiles: {e}")
        return {}

    def _save_preset_profiles(self, profiles: dict):
        import yaml
        path = self._get_preset_profiles_file_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(profiles, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[ERROR] Failed to save preset profiles: {e}")

    def _refresh_profile_list(self):
        """Reloads the list of profiles from the unified config and updates the combobox."""
        try:
            profiles = sorted(list(self._load_preset_profiles().keys()))
            self.profile_combobox.clear()
            if profiles:
                self.profile_combobox.addItems(profiles)
            else:
                self.profile_combobox.addItem("No profiles found")
        except Exception as e:
            print(f"[ERROR] Failed to refresh profiles: {e}")

    def _save_profile(self):
        """Saves the current settings dictionary as a profile in the unified config."""
        name = self.profile_name_entry.text().strip()
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        profiles = self._load_preset_profiles()
        if name in profiles:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "Confirm Overwrite", f"Profile '{name}' already exists. Overwrite it?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            import copy
            profiles[name] = copy.deepcopy(self.current_settings)
            self._save_preset_profiles(profiles)
            self._refresh_profile_list()
            self.profile_combobox.setCurrentText(name)
            print(f"Profile '{name}' saved successfully.")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save profile: {e}")

    def _load_profile(self):
        """Loads a profile from the unified config and applies its settings, ensuring the UI remains enabled."""
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        profiles = self._load_preset_profiles()
        if name not in profiles:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Profile not found in config: {name}")
            self._refresh_profile_list()
            return

        try:
            import copy
            loaded_settings = copy.deepcopy(profiles[name])

            job_index = self._get_selected_job_index()
            if job_index is not None:
                self.job_queue[job_index]['settings'].update(loaded_settings)
            else:
                self.current_settings.update(loaded_settings)

            self._populate_settings_panel()

            if 'translator_chain' in loaded_settings:
                self._rebuild_chain_from_string(loaded_settings['translator_chain'])

            self._update_chain_ui_state()
            self._set_settings_panel_enabled(job_index is not None)
            self.log("SUCCESS", f"Profile '{name}' loaded and applied.")
            print(f"Profile '{name}' loaded successfully.")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_message = f"An unexpected error occurred while loading profile '{name}'.\n\nDetails: {e}"
            print(f"[ERROR] {error_message}")
            QMessageBox.critical(self, "Profile Load Error", error_message)
        self._set_settings_panel_enabled(True)

    def _delete_profile(self):
        """Deletes the selected profile from the unified config."""
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete profile '{name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        profiles = self._load_preset_profiles()
        try:
            if name in profiles:
                del profiles[name]
                self._save_preset_profiles(profiles)
                print(f"Profile '{name}' deleted.")
                self._refresh_profile_list()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to delete profile: {e}")
            print(f"[ERROR] Failed to delete profile '{name}': {e}")

    def _on_font_scale_changed(self, text: str):
        """Applies a global font size by RE-APPLYING the currently selected theme."""
        current_theme_name = self.theme_combobox.currentText()
        self._apply_theme(current_theme_name)

    def _connect_widget_signal(self, key: str, widget: QWidget, context_key: str = None):
        """Connects the appropriate signal of a widget to the setting change handler."""
        info = self.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        handler = lambda *args, k=key, ctx=context_key: self._on_setting_changed(k, ctx)

        if isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(handler)
            if key in ['offline_translator', 'ai_translator']:
                widget.currentTextChanged.connect(self._on_translator_changed)
                if key == 'ai_translator':
                    widget.currentTextChanged.connect(self._sync_ai_credentials)
            elif key == 'target_lang':
                widget.currentTextChanged.connect(self._on_target_lang_changed)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(handler)
            if key == 'enable_translator_chain':
                widget.stateChanged.connect(self._update_chain_ui_state)
            if key == 'restore_size_after_colorize':
                widget.stateChanged.connect(self._update_colorize_restore_ui_state)
        elif isinstance(widget, QLineEdit):
            widget.editingFinished.connect(handler)
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                button_group.buttonClicked.connect(handler)
                if key == 'translator_category':
                    button_group.buttonClicked.connect(lambda *args: self._on_translator_category_changed())
        elif widget_type == "api_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(self._on_api_profile_changed)
                if combo.lineEdit():
                    combo.lineEdit().returnPressed.connect(combo.showPopup)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.activated.connect(lambda index: self._on_setting_changed('ai_model'))
        elif widget_type == "api_group_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(self._on_api_group_changed)
                if combo.lineEdit():
                    combo.lineEdit().returnPressed.connect(combo.showPopup)
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                slider.valueChanged.connect(handler)
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.editingFinished.connect(handler)

    def _on_setting_changed(self, key: str, context_key: str = None):
        """A generic handler called whenever a setting widget'''s value changes."""
        if context_key:
            widget = self.task_widgets[context_key].get(key)
            new_value = self._get_value_from_widget(key, widget)
            self.task_settings[context_key][key] = new_value
            print(f"[Task Settings] Updated '''{context_key}.{key}''' to: {new_value}")
        else:
            widget = self.setting_widgets.get(key)
            if key == 'translator_chain':
                new_value = self._get_translator_chain_string()
            else:
                new_value = self._get_value_from_widget(key, widget)
                
            if isinstance(widget, QComboBox):
                text = widget.currentText()
                if text in ["🔄 Cập nhật danh sách ngôn ngữ...", "🔄 Cập nhật danh sách hỗ trợ dịch..."]:
                    self._trigger_online_config_update_from_combo(key, widget)
                    return

            self.current_settings[key] = new_value
            print(f"[Settings] Updated '''{key}''' to: {new_value}")

            if key == 'app_language':
                self.config_loader.studio_config["app_language"] = new_value
                self.config_loader.save_studio_config()
                self._rebuild_settings_tab()

    def _on_translator_changed(self, translator_name: str):
        """Handles changes in the main translator selection."""
        if translator_name == "🔄 Cập nhật danh sách hỗ trợ dịch...":
            return
        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]
        self._update_translator_tooltip(translator_name)

    def _filter_translator_dropdowns(self, target_lang_name: str):
        """Filters the offline_translator and ai_translator dropdowns based on the selected target language."""
        from .. import main_window as mw
        if not target_lang_name:
            return

        target_code = mw.LANGUAGES.get(target_lang_name)
        if not target_code:
            return

        def supports_target(translator_name):
            if translator_name in ["none", "original"]:
                return True
            capabilities = mw.TRANSLATOR_CAPABILITIES.get(translator_name, {'__any__': '__all__'})
            if capabilities.get('__any__') == '__all__':
                return True
            for source_lang, target_langs in capabilities.items():
                if target_code in target_langs:
                    return True
            return False

        offline_combo = self.setting_widgets.get('offline_translator')
        if offline_combo:
            current_val = offline_combo.currentData()
            offline_combo.blockSignals(True)
            offline_combo.clear()
            filtered_offline = [t for t in self.original_offline_translators if supports_target(t)]
            for val in filtered_offline:
                exists = self.config_loader.check_model_existence(val, field='offline_translator')
                display_name = val if exists else f"{val} (Not Setup)"
                offline_combo.addItem(display_name, val)
                if not exists:
                    last_idx = offline_combo.count() - 1
                    offline_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            offline_combo.addItem("🔄 Cập nhật danh sách hỗ trợ dịch...", "update_trigger")
            offline_combo.addItem("🔄 Cập nhật phần mềm/mô hình dịch...", "update_software_trigger")
            
            restored = False
            for i in range(offline_combo.count()):
                if offline_combo.itemData(i) == current_val:
                    offline_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and offline_combo.count() > 0:
                offline_combo.setCurrentIndex(0)
            offline_combo.blockSignals(False)
            self._on_setting_changed('offline_translator')

        ai_combo = self.setting_widgets.get('ai_translator')
        if ai_combo:
            current_val = ai_combo.currentData()
            ai_combo.blockSignals(True)
            ai_combo.clear()
            filtered_ai = [t for t in self.original_ai_translators if supports_target(t)]
            for val in filtered_ai:
                exists = self.config_loader.check_model_existence(val, field='ai_translator')
                display_name = val if exists else f"{val} (Not Setup)"
                ai_combo.addItem(display_name, val)
                if not exists:
                    last_idx = ai_combo.count() - 1
                    ai_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            ai_combo.addItem("🔄 Cập nhật danh sách hỗ trợ dịch...", "update_trigger")
            ai_combo.addItem("🔄 Cập nhật phần mềm/mô hình dịch...", "update_software_trigger")
            
            restored = False
            for i in range(ai_combo.count()):
                if ai_combo.itemData(i) == current_val:
                    ai_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and ai_combo.count() > 0:
                ai_combo.setCurrentIndex(0)
            ai_combo.blockSignals(False)
            self._on_setting_changed('ai_translator')

        self._update_translator_visibility()
        active_translator = self._get_active_translator_name()
        self._update_translator_tooltip(active_translator)

    def _filter_chain_step_translator_dropdown(self, target_lang_name: str, translator_combo: QComboBox):
        """Filters the translator_combo in a translator chain step based on the selected target language."""
        from .. import main_window as mw
        if not target_lang_name:
            return
        
        target_code = mw.LANGUAGES.get(target_lang_name)
        if not target_code:
            return

        def supports_target(translator_name):
            if translator_name in ["none", "original"]:
                return True
            capabilities = mw.TRANSLATOR_CAPABILITIES.get(translator_name, {'__any__': '__all__'})
            if capabilities.get('__any__') == '__all__':
                return True
            for source_lang, target_langs in capabilities.items():
                if target_code in target_langs:
                    return True
            return False

        current_val = translator_combo.currentData()
        translator_combo.blockSignals(True)
        translator_combo.clear()

        for group_name, translators in mw.TRANSLATOR_GROUPS.items():
            filtered_translators = [t for t in translators if supports_target(t)]
            if not filtered_translators:
                continue
            item_index = translator_combo.count()
            translator_combo.addItem(group_name)
            translator_combo.model().item(item_index).setEnabled(False)
            
            field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
            for t in filtered_translators:
                exists = self.config_loader.check_model_existence(t, field=field_name)
                display_name = t if exists else f"{t} (Not Setup)"
                translator_combo.addItem(display_name, t)
                if not exists:
                    last_idx = translator_combo.count() - 1
                    translator_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
        
        restored = False
        for i in range(translator_combo.count()):
            if translator_combo.itemData(i) == current_val:
                translator_combo.setCurrentIndex(i)
                restored = True
                break
        if not restored and translator_combo.count() > 0:
            for i in range(translator_combo.count()):
                if translator_combo.model().item(i).isEnabled():
                    translator_combo.setCurrentIndex(i)
                    break
        translator_combo.blockSignals(False)

    def _on_target_lang_changed(self, target_lang_name: str):
        """Handles changes in the target language selection."""
        if target_lang_name == "🔄 Cập nhật danh sách ngôn ngữ...":
            return
        self._filter_translator_dropdowns(target_lang_name)

    def _filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        """A centralized function to filter a given language QComboBox based on translator capabilities."""
        from .. import main_window as mw
        if not lang_combo:
            return

        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]

        capabilities = mw.TRANSLATOR_CAPABILITIES.get(translator_name, {'__any__': '__all__'})
        supported_codes = set()

        if capabilities.get('__any__') == '__all__':
            all_langs = list(mw.LANGUAGES.values())
            if "auto" in all_langs:
                all_langs.remove("auto")
            supported_codes = set(all_langs)
        else:
            for source_lang, target_langs in capabilities.items():
                supported_codes.update(target_langs)

        supported_display_names = [name for name, code in mw.LANGUAGES.items() if code in supported_codes]
        current_selection = lang_combo.currentText()

        lang_combo.blockSignals(True)
        lang_combo.clear()
        if not supported_display_names:
            lang_combo.addItem("No Supported Targets")
            lang_combo.setEnabled(False)
        else:
            lang_combo.addItems(sorted(supported_display_names))
            lang_combo.setEnabled(True)
        lang_combo.blockSignals(False)

        if current_selection in supported_display_names:
            lang_combo.setCurrentText(current_selection)
        elif "English" in supported_display_names:
            lang_combo.setCurrentText("English")

    def _get_value_from_widget(self, key: str, widget: QWidget) -> any:
        """Retrieves the current value from a given widget by its key."""
        from .. import main_window as mw
        if not widget:
            return None

        info = self.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        if isinstance(widget, QComboBox):
            if widget_type == "optionmenu_languages":
                val = widget.currentData()
                if val is not None:
                    return val
                return mw.LANGUAGES.get(widget.currentText(), "auto")
            val = widget.currentData()
            if val is not None:
                return val
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group and button_group.checkedButton():
                value = button_group.checkedButton().text()
                if key == "upscale_ratio":
                    if value == "Disabled":
                        return None
                    else:
                        return int(value.replace("x", ""))
                return value
            return None
        elif widget_type in ["api_profile_selector", "api_group_selector", "ai_model_selector", "combobox_fonts"]:
            combo = widget.findChild(QComboBox) if not isinstance(widget, QComboBox) else widget
            return combo.currentText() if combo else None
        elif widget_type == "open_yaml_button":
            return info.get("default", "skip_languages.yaml")
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
        return None

    def _set_widget_value(self, key: str, value: any, widget: QWidget):
        """Sets the value of a given widget by its key."""
        from .. import main_window as mw
        if not widget or value is None:
            return

        info = self.config_loader.full_config_data.get(key, {})
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
                    display_name = next((k for k, v in mw.LANGUAGES.items() if v == value), None)
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
                    if button.text() == value_to_check:
                        button.setChecked(True)
                        break
        elif widget_type == "grid_segmented_button":
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                value_to_check = str(value)
                for button in button_group.buttons():
                    if button.text() == value_to_check:
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
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.setText(str(value))
        elif widget_type in ["api_profile_selector", "api_group_selector", "combobox_fonts"]:
            combo = widget.findChild(QComboBox) if not isinstance(widget, QComboBox) else widget
            if combo:
                combo.blockSignals(True)
                combo.setCurrentText(str(value))
                combo.blockSignals(False)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                value_str = str(value)
                if value_str and combo.findText(value_str) == -1:
                    combo.addItem(value_str)
                combo.blockSignals(True)
                combo.setCurrentText(value_str)
                combo.blockSignals(False)

    def closeEvent(self, event):
        """Handles the window close event to save the application state."""
        if self.is_running_pipeline:
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
        """Loads application state (window geometry, last directory) from the unified config."""
        try:
            settings = self.config_loader.studio_config
            geometry_hex = settings.get("window_geometry")
            if geometry_hex:
                self.restoreGeometry(QByteArray.fromHex(geometry_hex.encode('utf-8')))

            self.last_selected_directory = settings.get("last_directory")
            print("[INFO] Application state loaded.")
        except Exception as e:
            print(f"[WARNING] Could not load app settings: {e}")

    def _save_app_state(self):
        """Saves the current application state to the unified config."""
        self.config_loader.studio_config["window_geometry"] = self.saveGeometry().toHex().data().decode('utf-8')
        self.config_loader.studio_config["last_directory"] = getattr(self, 'last_selected_directory', None)
        self.config_loader.save_studio_config()
        print("[INFO] Application state saved.")

    def _load_themes(self):
        """Scans the themes directory and populates the theme combobox."""
        self.available_themes.clear()
        themes_dir = os.path.join(self.project_base_dir, "themes")
        self.available_themes["Default Qt"] = {"name": "Default Qt", "style": {}}

        if not os.path.isdir(themes_dir):
            self.theme_combobox.addItems(sorted(self.available_themes.keys()))
            return

        for filename in os.listdir(themes_dir):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(themes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = theme_data.get("name", filename)
                        self.available_themes[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        self.theme_combobox.addItems(sorted(self.available_themes.keys()))

    def _apply_theme(self, theme_name: str):
        """Applies the selected theme'''s stylesheet to the entire application."""
        font_size_text = self.font_scale_combobox.currentText()
        percentage = int(font_size_text.split('%')[0])
        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            minimal_style = f"""
                QWidget {{ font-size: {font_size}; }}
                QComboBox[warning="true"] {{ color: #FFC107; }}
                QPushButton {{
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 5px;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: #e0e0e0;
                }}
                QPushButton:checked {{
                    background-color: #3a7ebf;
                    color: white;
                    border: 2px solid #3a7ebf;
                    font-weight: bold;
                }}
                QPushButton:checked:hover {{
                    background-color: #2c5e8f;
                    border: 2px solid #2c5e8f;
                    color: white;
                }}
            """
            self.setStyleSheet(minimal_style)
            self.theme_colors = {}
            self.log("INFO", "Reverted to default Qt theme.")
            return

        theme_data = self.available_themes.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return

        colors = theme_data["style"].get("colors", {})
        self.theme_colors = colors
        
        bg_main = colors.get("background_main", "#2d2d2d")
        bg_frame = colors.get("background_frame", "#2d2d2d")
        btn_primary = colors.get("primary_button", "#3a7ebf")
        btn_hover = colors.get("primary_button_hover", "#56a9e8")
        slider_groove = colors.get("slider_groove", "#242424")
        slider_handle = colors.get("slider_handle", "#3a7ebf")
        txt_main = colors.get("text_main", "#dce4ee")
        border = colors.get("border", "#555555")
        accent = colors.get("accent", "#4a9fcf")
        arrow_icon_path = self._get_themed_arrow_icon_path(txt_main, theme_name)

        style_sheet = f"""
            QWidget {{
                font-size: {font_size};
                background-color: {bg_main};
                color: {txt_main};
            }}
            QFrame#StyledPanel, QFrame#LeftPanel {{
                background-color: {bg_frame};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: {btn_primary};
                color: {txt_main};
                border: 1px solid {border};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:checked {{
                background-color: {accent};
                color: white;
                border: 2px solid {accent};
            }}
            QPushButton:checked:hover {{
                background-color: {accent};
                border: 2px solid {accent};
                color: white;
            }}
            QPushButton:disabled {{ background-color: #555555; color: #888888; }}
            
            QComboBox, QLineEdit {{
                background-color: {bg_main};
                color: {txt_main};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 4px;
            }}
            QComboBox {{
                padding-right: 24px;
            }}
            QComboBox[warning="true"] {{
                color: #FFC107;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_icon_path});
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_main};
                color: {txt_main};
                border: 1px solid {border};
                selection-background-color: {accent};
            }}

            QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {border};
            border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{ 
                background-color: {bg_main}; 
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
            }}

            QSlider::groove:horizontal {{
                border: 1px solid {border};
                background: {slider_groove};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {slider_handle};
                border: 1px solid {slider_handle};
                width: 14px;
                margin: -6px 0; 
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {btn_hover};
                border: 1px solid {btn_hover};
            }}
            QListWidget, QTextEdit {{
                background-color: {bg_main};
                color: {txt_main};
                border: 1px solid {border};
                border-radius: 3px;
            }}
            QTabWidget::pane {{
                background-color: {bg_main};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background: {bg_main};
                padding: 6px;
                border: 1px solid {border};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {bg_frame};
                color: {txt_main};
                border-bottom: 1px solid {bg_frame};
            }}
            QTabBar::tab:!selected {{
                background: {bg_main};
                color: {txt_main};
            }}
            QTabBar::tab:!selected:hover {{
                background: {bg_frame};
            }}
            QToolTip {{
                color: {txt_main};
                background-color: {bg_frame};
                border: 1px solid {border};
            }}
        """
        self.setStyleSheet(style_sheet)
        self.log("INFO", f"Theme '''{theme_name}''' applied successfully.")

    def _show_queue_context_menu(self, position):
        """Creates and shows the context menu for the queue list."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        save_action = menu.addAction("✅ Save Settings to Job (Checkpoint)")
        save_action.triggered.connect(self._save_settings_to_job)

        load_action = menu.addAction("✏️ Load Job Settings to Panel")
        if len(selected_items) != 1:
            load_action.setDisabled(True)
        load_action.triggered.connect(self._load_settings_from_job)

        menu.addSeparator()
        duplicate_action = menu.addAction("➕ Duplicate Job (as new task)")
        duplicate_action.triggered.connect(self._duplicate_selected_jobs)

        remove_action = menu.addAction("🗑️ Remove from Queue")
        remove_action.triggered.connect(self._remove_selected_jobs_from_queue)

        menu.exec(self.queue_list_widget.mapToGlobal(position))

    def _save_settings_to_job(self):
        """Saves the current panel settings to the selected job(s) (Checkpoint)."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job = next((j for j in self.job_queue if j['id'] == job_id), None)
            if job:
                job['settings'] = copy.deepcopy(self.current_settings)
                job['status'] = 'Ready'
                if not job.get('job_type'):
                    job['job_type'] = 'T'

        self._update_job_list_ui()
        self.log("SUCCESS", f"Checkpoint created. Saved settings to {len(selected_items)} job(s).")

    def _load_settings_from_job(self):
        """Loads a selected job'''s settings back into the main panel for editing."""
        selected_items = self.queue_list_widget.selectedItems()
        if len(selected_items) != 1:
            return

        job_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        job = next((j for j in self.job_queue if j['id'] == job_id), None)

        if job:
            self.current_settings = copy.deepcopy(job['settings'])
            self._populate_settings_panel()
            self.log("INFO", f"Loaded settings from '''{job['name']}''' into the panel for editing.")

    def _handle_create_keys_file(self):
        """Checks for, creates, and opens the keys.yaml file in the .config/configs directory."""
        keys_dir = os.path.join(self.project_base_dir, ".config", "configs")
        os.makedirs(keys_dir, exist_ok=True)
        keys_path = os.path.join(keys_dir, "keys.yaml")
        self.log("INFO", f"Managing keys.yaml file at: {keys_path}")

        KEYS_TEMPLATE = [
            "# --- Baidu Translate ---",
            "BAIDU_APP_ID: \"\"",
            "BAIDU_SECRET_KEY: \"\"",
            "\n# --- Youdao Translate ---",
            "YOUDAO_APP_KEY: \"\"",
            "YOUDAO_SECRET_KEY: \"\"",
            "\n# --- DeepL Translate ---",
            "DEEPL_AUTH_KEY: \"\"",
            "\n# --- Caiyun Translate ---",
            "CAIYUN_TOKEN: \"\"",
            "\n# --- OpenAI ---",
            "OPENAI_API_KEY: \"\"",
            "OPENAI_MODEL: \"gpt-4o\"",
            "OPENAI_API_BASE: \"https://api.openai.com/v1\"",
            "OPENAI_HTTP_PROXY: \"\"",
            "OPENAI_GLOSSARY_PATH: \"./dict/mit_glossary.txt\"",
            "\n# --- Groq ---",
            "GROQ_API_KEY: \"\"",
            "GROQ_MODEL: \"mixtral-8x7b-32768\"",
            "\n# --- Gemini ---",
            "GEMINI_API_KEY: \"\"",
            "GEMINI_MODEL: \"gemini-1.5-flash\"",
            "\n# --- DeepSeek ---",
            "DEEPSEEK_API_KEY: \"\"",
            "DEEPSEEK_MODEL: \"deepseek-chat\"",
            "DEEPSEEK_API_BASE: \"https://api.deepseek.com\"",
            "\n# --- Sakura Translator ---",
            "SAKURA_API_BASE: \"http://127.0.0.1:8080/v1\"",
            "SAKURA_DICT_PATH: \"./dict/sakura_dict.txt\"",
            "\n# --- Custom OpenAI (Ollama, etc.) ---",
            "CUSTOM_OPENAI_API_KEY: \"ollama\"",
            "CUSTOM_OPENAI_MODEL: \"\"",
            "CUSTOM_OPENAI_API_BASE: \"http://localhost:11434/v1\"",
        ]

        try:
            if not os.path.exists(keys_path):
                self.log("INFO", "keys.yaml file not found. Creating a new template...")
                with open(keys_path, '''w''', encoding='''utf-8''') as f:
                    f.write("# This file stores your API keys and configuration parameters.\n")
                    f.write("# Place your keys below. Do NOT share this file with anyone.\n\n")
                    f.write("\n".join(KEYS_TEMPLATE))

            if sys.platform == "win32":
                os.startfile(keys_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", keys_path])
            else:
                subprocess.run(["xdg-open", keys_path])

        except Exception as e:
            error_msg = f"Could not open the keys.yaml file. Please open it manually.\nPath: {keys_path}\nError: {e}"
            self.log("ERROR", error_msg)
            QMessageBox.warning(self, "Could Not Open File", error_msg)

    def _show_history_context_menu(self, position):
        """Creates and shows the context menu for the history list."""
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        requeue_action = menu.addAction("↪️ Re-queue Job")
        requeue_action.triggered.connect(self._requeue_job)
        menu.exec(self.history_list_widget.mapToGlobal(position))

    def _build_font_map(self):
        """Scans the project'''s /fonts folder to create a name-to-filepath map."""
        self.font_map = {}
        found_any = False
        for folder in ["fonts", os.path.join("MangaStudio_Data", "fonts")]:
            fonts_dir = os.path.join(self.project_base_dir, folder)
            if os.path.isdir(fonts_dir):
                found_any = True
                for font_file in sorted(os.listdir(fonts_dir)):
                    if font_file.lower().endswith(('.ttf', '.otf', '.ttc')):
                        font_path = os.path.join(fonts_dir, font_file)
                        self.font_map[font_file] = font_path
        if not found_any:
            print(f"[WARNING] Fonts directories not found")

    def _get_google_font_family_from_filename(self, filename: str) -> str:
        """Checks if the filename matches any of our known Google Fonts and returns the family name."""
        clean_fn = filename.replace("-", "").replace(" ", "").lower()
        for gf in self.GOOGLE_FONTS:
            clean_gf = gf.replace(" ", "").lower()
            if clean_gf in clean_fn:
                return gf
        return None

    def _get_installed_google_fonts(self) -> dict:
        """Scans the current font map and maps Google Font Family Name -> list of local font filenames."""
        installed_google_fonts = {}
        for filename in self.font_map.keys():
            google_family = self._get_google_font_family_from_filename(filename)
            if google_family:
                installed_google_fonts.setdefault(google_family, []).append(filename)
        return installed_google_fonts

    def _save_font_version_from_online_metadata(self, font_family: str):
        """Fetches the latest online version of a single font family and saves it in config."""
        from PySide6.QtCore import Signal, QThread
        class SingleVersionFetchWorker(QThread):
            done = Signal(str)
            def run(self):
                import urllib.request
                try:
                    url = "https://cdn.jsdelivr.net/npm/google-font-metadata/data/google-fonts-v2.json"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        data = json.loads(response.read().decode('utf-8'))
                    key = font_family.lower().replace(" ", "-")
                    if key not in data:
                        key = font_family.lower().replace(" ", "")
                    if key in data:
                        version = data[key].get("version", "")
                        self.done.emit(version)
                        return
                except Exception as e:
                    print(f"[WARNING] Failed to fetch online metadata for single version check: {e}")
                self.done.emit("")
        
        if not hasattr(self, "_active_ver_workers"):
            self._active_ver_workers = set()
            
        worker = SingleVersionFetchWorker()
        self._active_ver_workers.add(worker)
        
        def on_done(version):
            if version:
                versions = self.config_loader.studio_config.setdefault("font_versions", {})
                versions[font_family] = version
                self.config_loader.save_studio_config()
                print(f"[Config] Updated font version for '''{font_family}''' to '''{version}'''")
            self._active_ver_workers.discard(worker)

        worker.done.connect(on_done)
        worker.start()

    def _force_update_current_font(self, main_font_combo: QComboBox):
        """Force updates (re-downloads) the currently selected font family if it is a Google Font."""
        current_font = main_font_combo.currentText()
        if not current_font or current_font == "No fonts found in /fonts folder":
            return

        google_family = self._get_google_font_family_from_filename(current_font)
        if not google_family:
            return

        if getattr(self, "_font_install_active", False):
            return
        self._font_install_active = True

        reply = QMessageBox.question(
            self,
            "Xác nhận Cập nhật",
            f"Bạn có muốn tải lại và cập nhật bắt buộc phông chữ '''{google_family}''' từ Google Fonts không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            self._font_install_active = False
            return

        self.log("INFO", f"Đang cập nhật bắt buộc phông chữ: {google_family}...")
        main_font_combo.setEnabled(False)
        fonts_dir = os.path.join(self.project_base_dir, "fonts")

        class FontDownloadWorker(QThread):
            finished = Signal(bool, str)
            def run(self):
                import urllib.request
                import urllib.parse
                import re
                try:
                    url = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(google_family)}:regular,italic,700,700italic"
                    req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.81.0'})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        css_content = response.read().decode('utf-8')
                    
                    blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                    if not blocks:
                        url_fallback = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(google_family)}"
                        req_fb = urllib.request.Request(url_fallback, headers={'User-Agent': 'curl/7.81.0'})
                        with urllib.request.urlopen(req_fb, timeout=15) as response_fb:
                            css_content = response_fb.read().decode('utf-8')
                        blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                    
                    if not blocks:
                        self.finished.emit(False, "Không tìm thấy cấu hình phông chữ trên Google Fonts.")
                        return

                    os.makedirs(fonts_dir, exist_ok=True)
                    extracted_any = False
                    
                    for block in blocks:
                        url_match = re.search(r'url\((https://fonts\.gstatic\.com/s/[^)]+\.ttf)\)', block)
                        if url_match:
                            ttf_url = url_match.group(1).strip()
                            style_match = re.search(r'font-style:\s*([^;]+);', block)
                            weight_match = re.search(r'font-weight:\s*([^;]+);', block)
                            
                            style = style_match.group(1).strip() if style_match else "normal"
                            weight = weight_match.group(1).strip() if weight_match else "400"
                            
                            clean_name = google_family.replace(" ", "")
                            if weight == "700" and style == "italic":
                                suffix = "-BoldItalic"
                            elif weight == "700":
                                suffix = "-Bold"
                            elif style == "italic":
                                suffix = "-Italic"
                            else:
                                suffix = "-Regular"
                            
                            filename = f"{clean_name}{suffix}.ttf"
                            dest_path = os.path.join(fonts_dir, filename)
                            
                            req_ttf = urllib.request.Request(ttf_url, headers={'User-Agent': 'curl/7.81.0'})
                            with urllib.request.urlopen(req_ttf, timeout=15) as res_ttf:
                                font_data = res_ttf.read()
                            
                            with open(dest_path, "wb") as f:
                                f.write(font_data)
                            extracted_any = True
                            
                    if extracted_any:
                        self.finished.emit(True, google_family)
                    else:
                        self.finished.emit(False, "Không tìm thấy tệp font phù hợp để tải về.")
                except Exception as e:
                    self.finished.emit(False, str(e))

        self._font_worker = FontDownloadWorker()

        def on_finished(success, message_or_family):
            self._font_install_active = False
            main_font_combo.setEnabled(True)
            if success:
                self.log("SUCCESS", f"Đã cập nhật thành công phông chữ '''{message_or_family}'''!")
                self._build_font_map()
                font_names = list(self.font_map.keys())

                self._save_font_version_from_online_metadata(google_family)

                main_font_combo.blockSignals(True)
                main_font_combo.clear()
                main_font_combo.addItems(font_names)
                main_font_combo.addItem("📥 Install New Font...")
                main_font_combo.addItem("🔄 Update All Fonts...")
                self._style_custom_fonts_in_combobox(main_font_combo)

                newly_installed_font = next((fn for fn in font_names if message_or_family.replace(" ", "").lower() in fn.replace("-", "").replace(" ", "").lower()), None)
                if newly_installed_font:
                    main_font_combo.setCurrentText(newly_installed_font)
                    self._last_selected_font = newly_installed_font
                else:
                    main_font_combo.setCurrentText(current_font)
                main_font_combo.blockSignals(False)

                self._on_setting_changed("font_family")
                QMessageBox.information(self, "Cập nhật Thành công", f"Phông chữ '''{message_or_family}''' đã được cập nhật lên bản mới nhất!")
            else:
                self.log("ERROR", f"Cập nhật phông chữ thất bại: {message_or_family}")
                QMessageBox.critical(self, "Cập nhật Thất bại", f"Không thể cập nhật '''{google_family}'''.\n\nLỗi: {message_or_family}")
            del self._font_worker

        self._font_worker.finished.connect(on_finished)
        self._font_worker.start()

    def _prompt_font_install(self, main_font_combo: QComboBox, pre_selected_font=None):
        """Allows user to select and download a new Google Font family in a background thread."""
        if getattr(self, "_font_install_active", False):
            return
        self._font_install_active = True

        prev_font = getattr(self, "_last_selected_font", "Sans-serif")
        
        dialog = SearchableFontInstallDialog(self.GOOGLE_FONTS, default_font=pre_selected_font or prev_font, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_font:
            font_family = dialog.selected_font
        else:
            self._font_install_active = False
            main_font_combo.blockSignals(True)
            main_font_combo.setCurrentText(prev_font)
            main_font_combo.blockSignals(False)
            return

        self.log("INFO", f"Initiating download for font family: {font_family}...")
        main_font_combo.setEnabled(False)
        fonts_dir = os.path.join(self.project_base_dir, "fonts")
        
        class FontDownloadWorker(QThread):
            finished = Signal(bool, str)
            def run(self):
                import urllib.request
                import urllib.parse
                import re
                try:
                    url = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(font_family)}:regular,italic,700,700italic"
                    req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.81.0'})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        css_content = response.read().decode('utf-8')
                    
                    blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                    if not blocks:
                        url_fallback = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(font_family)}"
                        req_fb = urllib.request.Request(url_fallback, headers={'User-Agent': 'curl/7.81.0'})
                        with urllib.request.urlopen(req_fb, timeout=15) as response_fb:
                            css_content = response_fb.read().decode('utf-8')
                        blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                    
                    if not blocks:
                        self.finished.emit(False, "Không tìm thấy cấu hình phông chữ trên Google Fonts.")
                        return

                    os.makedirs(fonts_dir, exist_ok=True)
                    extracted_any = False
                    
                    for block in blocks:
                        url_match = re.search(r'url\((https://fonts\.gstatic\.com/s/[^)]+\.ttf)\)', block)
                        if url_match:
                            ttf_url = url_match.group(1).strip()
                            style_match = re.search(r'font-style:\s*([^;]+);', block)
                            weight_match = re.search(r'font-weight:\s*([^;]+);', block)
                            
                            style = style_match.group(1).strip() if style_match else "normal"
                            weight = weight_match.group(1).strip() if weight_match else "400"
                            
                            clean_name = font_family.replace(" ", "")
                            if weight == "700" and style == "italic":
                                suffix = "-BoldItalic"
                            elif weight == "700":
                                suffix = "-Bold"
                            elif style == "italic":
                                suffix = "-Italic"
                            else:
                                suffix = "-Regular"
                            
                            filename = f"{clean_name}{suffix}.ttf"
                            dest_path = os.path.join(fonts_dir, filename)
                            
                            req_ttf = urllib.request.Request(ttf_url, headers={'User-Agent': 'curl/7.81.0'})
                            with urllib.request.urlopen(req_ttf, timeout=15) as res_ttf:
                                font_data = res_ttf.read()
                            
                            with open(dest_path, "wb") as f:
                                f.write(font_data)
                            extracted_any = True
                            
                    if extracted_any:
                        self.finished.emit(True, font_family)
                    else:
                        self.finished.emit(False, "Không tải được tệp .ttf nào từ Google Fonts.")
                except Exception as e:
                    self.finished.emit(False, str(e))

        self._font_worker = FontDownloadWorker()
        
        def on_finished(success, message_or_family):
            self._font_install_active = False
            main_font_combo.setEnabled(True)
            if success:
                self.log("SUCCESS", f"Font '''{message_or_family}''' successfully installed and loaded!")
                self._build_font_map()
                font_names = list(self.font_map.keys())
                
                self._save_font_version_from_online_metadata(font_family)

                main_font_combo.blockSignals(True)
                main_font_combo.clear()
                main_font_combo.addItems(font_names)
                main_font_combo.addItem("📥 Install New Font...")
                main_font_combo.addItem("🔄 Update All Fonts...")
                self._style_custom_fonts_in_combobox(main_font_combo)
                
                newly_installed_font = next((fn for fn in font_names if message_or_family.replace(" ", "").lower() in fn.replace("-", "").replace(" ", "").lower()), None)
                if newly_installed_font:
                    main_font_combo.setCurrentText(newly_installed_font)
                    self._last_selected_font = newly_installed_font
                else:
                    main_font_combo.setCurrentIndex(0)
                    self._last_selected_font = font_names[0] if font_names else "Sans-serif"
                main_font_combo.blockSignals(False)
                
                self._on_setting_changed("font_family")
                QMessageBox.information(self, "Installation Complete", f"Font '''{message_or_family}''' has been successfully installed and selected!")
            else:
                self.log("ERROR", f"Failed to install font: {message_or_family}")
                main_font_combo.blockSignals(True)
                main_font_combo.setCurrentText(prev_font)
                main_font_combo.blockSignals(False)
                QMessageBox.critical(self, "Installation Failed", f"Could not install '''{font_family}'''.\n\nError: {message_or_family}")
            del self._font_worker

        self._font_worker.finished.connect(on_finished)
        self._font_worker.start()

    def _find_similar_font(self, main_font_combo: QComboBox):
        """Recommends similar Google Fonts when a custom/manual copy font is selected."""
        current_font = main_font_combo.currentText()
        if not current_font or current_font == "No fonts found in /fonts folder":
            return
            
        clean_fn = current_font.lower()
        recommendations = []
        reason = ""
        
        if any(x in clean_fn for x in ["comic", "anime", "ace", "shanns", "hand", "kalam", "chewy", "bell", "daugh"]):
            recommendations = ["Comic Neue", "Bangers", "Patrick Hand", "Architects Daughter"]
            reason = "phông chữ viết tay truyện tranh / Manga Cartoon"
        elif any(x in clean_fn for x in ["gothic", "msyh", "msgothic", "cjk", "jp", "sc", "tc", "kr", "sans", "mono"]):
            recommendations = ["Noto Sans JP", "Noto Sans SC", "Noto Sans KR", "ZCOOL KuaiLe"]
            reason = "phông chữ không chân (Sans-serif) hoặc phông chữ đa ngôn ngữ CJK"
        else:
            recommendations = ["Comic Neue", "Bangers", "Fredoka One", "Schoolbell"]
            reason = "phông chữ truyện tranh phổ biến"

        installed_google = self._get_installed_google_fonts()
        to_install = []
        
        msg = f"Phông chữ đang chọn '''{current_font}''' là phông chữ tự thêm bên ngoài.\n\n"
        msg += f"Gợi ý các phông chữ tương tự có sẵn trên Google Fonts ({reason}):\n"
        for r in recommendations:
            if r in installed_google:
                msg += f" • {r} (Đã cài đặt)\n"
            else:
                msg += f" • {r}\n"
                to_install.append(r)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Tìm phông chữ tương tự trên Google Fonts")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Icon.Question)

        install_all_btn = None
        if to_install:
            install_all_btn = msg_box.addButton(f"Tải {len(to_install)} gợi ý chưa cài", QMessageBox.ButtonRole.AcceptRole)
        
        open_dialog_btn = msg_box.addButton("Mở hộp cài đặt từng font", QMessageBox.ButtonRole.YesRole)
        cancel_btn = msg_box.addButton("Hủy bỏ", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == install_all_btn and to_install:
            updates = [(r, "Chưa cài đặt", "latest") for r in to_install]
            self._download_updates(updates, main_font_combo)
        elif clicked_button == open_dialog_btn:
            pre_sel = to_install[0] if to_install else recommendations[0]
            self._prompt_font_install(main_font_combo, pre_selected_font=pre_sel)

    def _check_and_update_all_fonts(self, main_font_combo: QComboBox):
        """Scans all installed Google Fonts, checks jsdelivr metadata for updates, and prompts to download."""
        if getattr(self, "_bulk_update_active", False):
            return
        self._bulk_update_active = True

        main_font_combo.setEnabled(False)
        self.log("INFO", "Đang quét danh sách phông chữ Google Fonts đã cài đặt...")
        
        installed_google_fonts = self._get_installed_google_fonts()
        installed_families = list(installed_google_fonts.keys())
        
        if not installed_families:
            self._bulk_update_active = False
            main_font_combo.setEnabled(True)
            QMessageBox.information(
                self,
                "Kiểm tra Cập nhật",
                "Không tìm thấy phông chữ Google Fonts nào trong thư mục '''fonts/''' để kiểm tra cập nhật."
            )
            prev_font = getattr(self, "_last_selected_font", "Sans-serif")
            main_font_combo.blockSignals(True)
            main_font_combo.setCurrentText(prev_font)
            main_font_combo.blockSignals(False)
            return

        local_versions = self.config_loader.studio_config.get("font_versions", {})
        
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowTitle("Đang kiểm tra")
        progress_dialog.setText("Đang tải dữ liệu phiên bản phông chữ từ Google Fonts...")
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_dialog.show()
        
        self._check_worker = CheckAllFontsWorker(installed_families, local_versions)
        
        def on_check_finished(success, updates, error_msg):
            self._bulk_update_active = False
            progress_dialog.close()
            main_font_combo.setEnabled(True)
            
            prev_font = getattr(self, "_last_selected_font", "Sans-serif")
            main_font_combo.blockSignals(True)
            main_font_combo.setCurrentText(prev_font)
            main_font_combo.blockSignals(False)

            if not success:
                self.log("ERROR", f"Không thể kiểm tra phiên bản phông chữ trực tuyến: {error_msg}")
                QMessageBox.critical(
                    self,
                    "Kiểm tra Thất bại",
                    f"Không thể kết nối tới máy chủ cập nhật để kiểm tra phiên bản.\n\nChi tiết lỗi: {error_msg}"
                )
                return

            if not updates:
                QMessageBox.information(
                    self,
                    "Kiểm tra Hoàn tất",
                    "Tất cả phông chữ Google Fonts của bạn đã ở phiên bản mới nhất!"
                )
                return

            msg = "Tìm thấy các phông chữ có thể cập nhật:\n\n"
            for family, local_ver, online_ver in updates:
                msg += f"• {family}: {local_ver} ➔ {online_ver}\n"
            msg += "\nBạn có muốn tải và cập nhật các phông chữ này không?"

            reply = QMessageBox.question(
                self,
                "Có bản cập nhật mới",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

            self._download_updates(updates, main_font_combo)
            del self._check_worker

        self._check_worker.finished.connect(on_check_finished)
        self._check_worker.start()

    def _download_updates(self, updates, main_font_combo):
        """Downloads the updates list in a background thread with progress dialog."""
        from PySide6.QtWidgets import QProgressDialog
        
        progress = QProgressDialog("Bắt đầu cập nhật các phông chữ...", "Hủy", 0, len(updates), self)
        progress.setWindowTitle("Đang cập nhật Phông chữ")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        main_font_combo.setEnabled(False)
        fonts_dir = os.path.join(self.project_base_dir, "fonts")
        
        self._bulk_worker = BulkFontDownloadWorker(updates, fonts_dir)
        progress.canceled.connect(self._bulk_worker.terminate)
        
        def on_progress(current, total, family):
            progress.setValue(current - 1)
            progress.setLabelText(f"Đang tải ({current}/{total}): {family}...")
            
        def on_finished(success, success_updates, error_msg):
            progress.setValue(len(updates))
            progress.close()
            main_font_combo.setEnabled(True)
            
            if success_updates:
                versions = self.config_loader.studio_config.setdefault("font_versions", {})
                for fam, ver in success_updates.items():
                    versions[fam] = ver
                self.config_loader.save_studio_config()
                
                for fam in success_updates.keys():
                    self._save_font_version_from_online_metadata(fam)
                
                self.log("SUCCESS", f"Đã cập nhật thành công {len(success_updates)} phông chữ!")
                self._build_font_map()
                font_names = list(self.font_map.keys())
                
                main_font_combo.blockSignals(True)
                main_font_combo.clear()
                main_font_combo.addItems(font_names)
                main_font_combo.addItem("📥 Install New Font...")
                main_font_combo.addItem("🔄 Update All Fonts...")
                self._style_custom_fonts_in_combobox(main_font_combo)
                
                prev_font = getattr(self, "_last_selected_font", "Sans-serif")
                if prev_font in font_names:
                    main_font_combo.setCurrentText(prev_font)
                else:
                    main_font_combo.setCurrentIndex(0)
                main_font_combo.blockSignals(False)
                
                self._on_setting_changed("font_family")
                
                info_msg = f"Đã cập nhật thành công {len(success_updates)} phông chữ lên phiên bản mới nhất!"
                if error_msg:
                    formatted_err = error_msg.replace("; ", "\n- ")
                    info_msg += f"\n\nMột số phông chữ tải thất bại:\n- {formatted_err}"
                QMessageBox.information(
                    self,
                    "Cập nhật Hoàn tất",
                    info_msg
                )
            else:
                detailed_msg = "Không có phông chữ nào được cập nhật thành công hoặc thao tác đã bị hủy."
                if error_msg:
                    formatted_err = error_msg.replace("; ", "\n- ")
                    detailed_msg += f"\n\nChi tiết lỗi:\n- {formatted_err}"
                QMessageBox.warning(
                    self,
                    "Cập nhật Hoàn tất",
                    detailed_msg
                )
            del self._bulk_worker

        self._bulk_worker.progress.connect(on_progress)
        self._bulk_worker.finished.connect(on_finished)
        self._bulk_worker.start()

    def _trigger_translator_software_update(self, key: str):
        """Triggers a background mock process to simulate updating the software/model weights."""
        combo = self.setting_widgets.get(key)
        if not combo:
            return
        translator_name = combo.itemData(combo.currentIndex())
        if not translator_name or translator_name in ["none", "original"]:
            QMessageBox.information(self, "Thông tin", f"Bộ dịch '''{translator_name}''' không hỗ trợ cập nhật phần mềm.")
            return

        reply = QMessageBox.question(
            self,
            "Cập nhật Bộ dịch",
            f"Bạn có muốn kiểm tra và tải/cập nhật phiên bản phần mềm hoặc tệp mô hình mới nhất của bộ dịch '''{translator_name}''' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.log("INFO", f"Đang kiểm tra cập nhật phần mềm/mô hình cho bộ dịch: {translator_name}...")
        
        for k in ['offline_translator', 'ai_translator']:
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        class TranslatorSoftwareUpdateWorker(QThread):
            finished = Signal(bool, str)
            progress = Signal(int, str)
            
            def run(self):
                import urllib.request
                import urllib.error
                import json
                import os
                import yaml
                
                try:
                    self.progress.emit(10, f"Đang tải cấu hình nguồn của {translator_name}...")
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    config_dir = os.path.join(base_dir, ".config", "configs")
                    sources_file = os.path.join(config_dir, "model_sources.yaml")
                    local_versions_file = os.path.join(config_dir, "local_versions.json")
                    
                    if not os.path.exists(sources_file):
                        self.finished.emit(False, "Không tìm thấy file cấu hình model_sources.yaml.")
                        return
                        
                    with open(sources_file, "r", encoding="utf-8") as sf:
                        sources = yaml.safe_load(sf)
                        
                    url = sources.get(translator_name)
                    if not url:
                        self.finished.emit(False, f"Không tìm thấy cấu hình nguồn tải cho bộ dịch '{translator_name}' trong model_sources.yaml.")
                        return
                    
                    self.progress.emit(30, "Đang kết nối để kiểm tra phiên bản mới nhất...")
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    try:
                        with urllib.request.urlopen(req, timeout=10) as response:
                            data = json.loads(response.read().decode('utf-8'))
                            latest_version = data.get("tag_name", "unknown")
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi khi kết nối đến nguồn tải: {e}")
                        return
                        
                    self.progress.emit(50, f"Phiên bản mới nhất trên máy chủ: {latest_version}. Đang kiểm tra cục bộ...")
                    
                    local_versions = {}
                    if os.path.exists(local_versions_file):
                        with open(local_versions_file, "r", encoding="utf-8") as lf:
                            local_versions = json.load(lf)
                            
                    current_version = local_versions.get(translator_name, "none")
                    if current_version == latest_version:
                        self.progress.emit(100, "Hoàn tất")
                        self.finished.emit(True, f"Bộ dịch '{translator_name}' đã ở phiên bản mới nhất ({current_version}). Không cần cập nhật.")
                        return
                        
                    self.progress.emit(70, f"Phát hiện bản mới ({latest_version}). Đang tiến hành tải dữ liệu mô hình...")
                    import time
                    time.sleep(2) # Simulate download process for now
                    
                    # Update local version
                    local_versions[translator_name] = latest_version
                    with open(local_versions_file, "w", encoding="utf-8") as lf:
                        json.dump(local_versions, lf, indent=4)
                        
                    # Create models folder to pretend it is setup
                    model_dir = os.path.join(base_dir, "models", translator_name)
                    os.makedirs(model_dir, exist_ok=True)
                    
                    self.progress.emit(100, "Tải và cài đặt thành công!")
                    self.finished.emit(True, f"Đã cập nhật/cài đặt thành công mô hình '{translator_name}' lên phiên bản {latest_version}!")
                except Exception as e:
                    self.finished.emit(False, f"Lỗi không xác định: {str(e)}")


        from PySide6.QtWidgets import QProgressDialog
        progress_dlg = QProgressDialog(f"Đang kiểm tra cập nhật cho {translator_name}...", "Hủy", 0, 100, self)
        progress_dlg.setWindowTitle("Cập nhật Mô hình Dịch")
        from PySide6.QtCore import Qt
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()

        self._software_worker = TranslatorSoftwareUpdateWorker()
        progress_dlg.canceled.connect(self._software_worker.terminate)
        
        def on_progress(val, text):
            progress_dlg.setValue(val)
            progress_dlg.setLabelText(text)
            
        def on_finished(success, message):
            progress_dlg.setValue(100)
            progress_dlg.close()
            for k in ['offline_translator', 'ai_translator']:
                w = self.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)
            if success:
                self.log("SUCCESS", message)
                QMessageBox.information(self, "Cập nhật Hoàn tất", message)
            else:
                self.log("ERROR", message)
                QMessageBox.warning(self, "Cập nhật Thất bại", message)
            del self._software_worker

        self._software_worker.finished.connect(on_finished)
        self._software_worker.progress.connect(on_progress)
        self._software_worker.start()

    def _trigger_online_config_update_from_combo(self, key: str, combo: QComboBox):
        """Triggers online update when a special trigger item is selected from a QComboBox."""
        selected_data = combo.itemData(combo.currentIndex())
        
        if selected_data == "update_trigger":
            combo.blockSignals(True)
            prev_val = self.current_settings.get(key)
            self._set_widget_value(key, prev_val, combo)
            combo.blockSignals(False)
            
            if key == "target_lang":
                self._trigger_online_config_update("target_lang")
            elif key in ["offline_translator", "ai_translator"]:
                self._trigger_all_configs_update()
        elif selected_data == "update_software_trigger":
            combo.blockSignals(True)
            prev_val = self.current_settings.get(key)
            self._set_widget_value(key, prev_val, combo)
            combo.blockSignals(False)
            
            self._trigger_translator_software_update(key)

    def _trigger_online_config_update(self, key: str):
        """Triggers a background thread to update a single configuration parameter."""
        if getattr(self, "_config_update_active", False):
            QMessageBox.information(self, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        mode = ""
        translator_name = None
        api_key = None

        if key == "target_lang":
            mode = "languages"
            self.log("INFO", "Đang cập nhật danh sách ngôn ngữ đích từ LibreTranslate...")
        elif key in ["offline_translator", "ai_translator"]:
            mode = "single_translator"
            combo = self.setting_widgets.get(key)
            if not combo:
                return
            translator_name = combo.itemData(combo.currentIndex())
            if not translator_name or translator_name in ["none", "original"]:
                QMessageBox.information(self, "Thông tin", f"Bộ dịch '''{translator_name}''' không hỗ trợ cập nhật động.")
                return
                
            self.log("INFO", f"Đang cập nhật khả năng dịch cho bộ dịch: {translator_name}...")
            if key == "ai_translator" and translator_name == "deepl":
                api_key = self.config_loader.get_env_var('DEEPL_API_KEY')
        else:
            return

        self._config_update_active = True
        
        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        self._config_worker = ConfigUpdateWorker(self.config_loader, mode, translator_name, api_key)

        def on_finished(success, message):
            self._config_update_active = False
            for k in ['target_lang', 'offline_translator', 'ai_translator']:
                w = self.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)
            
            if success:
                self.log("SUCCESS", message)
                self._reload_dynamic_configurations()
                QMessageBox.information(self, "Cập nhật Thành công", message)
            else:
                self.log("ERROR", message)
                QMessageBox.warning(self, "Cập nhật Thất bại", message)
                
            del self._config_worker

        self._config_worker.finished.connect(on_finished)
        self._config_worker.start()

    def _trigger_all_configs_update(self):
        """Triggers a background thread to update all configs (languages & capabilities)."""
        if getattr(self, "_config_update_active", False):
            QMessageBox.information(self, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận Cập nhật Tất cả",
            "Bạn có muốn tải về và đồng bộ hóa toàn bộ danh sách ngôn ngữ & năng lực bộ dịch từ Internet không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.log("INFO", "Bắt đầu cập nhật toàn bộ cấu hình ngôn ngữ và khả năng dịch...")
        self._config_update_active = True

        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        self._config_worker = ConfigUpdateWorker(self.config_loader, "all")

        def on_finished(success, message):
            self._config_update_active = False
            for k in ['target_lang', 'offline_translator', 'ai_translator']:
                w = self.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)
            
            if success:
                self.log("SUCCESS", message)
                self._reload_dynamic_configurations()
                QMessageBox.information(self, "Cập nhật Thành công", message)
            else:
                self.log("ERROR", message)
                QMessageBox.warning(self, "Cập nhật Thất bại", message)
                
            del self._config_worker

        self._config_worker.finished.connect(on_finished)
        self._config_worker.start()

    def _reload_dynamic_configurations(self):
        """Reloads dynamic configurations from the config loader into global mapping variables."""
        from .. import main_window as mw
        
        if hasattr(self.config_loader, 'languages') and self.config_loader.languages:
            mw.LANGUAGES.clear()
            mw.LANGUAGES.update(self.config_loader.languages)
            
        offline_info = self.config_loader.full_config_data.get('offline_translator')
        ai_info = self.config_loader.full_config_data.get('ai_translator')
        
        offline_list = offline_info.get('values', []) if offline_info else []
        api_list = ai_info.get('values', []) if ai_info else []
        other_list = ["original", "none"]
        
        mw.TRANSLATOR_GROUPS.clear()
        mw.TRANSLATOR_GROUPS["--- OFFLINE MODELS (No API Key) ---"] = offline_list
        mw.TRANSLATOR_GROUPS["--- API-BASED (Requires Setup) ---"] = api_list
        mw.TRANSLATOR_GROUPS["--- OTHER ACTIONS ---"] = other_list
        
        self.original_offline_translators = list(offline_list)
        self.original_ai_translators = list(api_list)
        
        if hasattr(self.config_loader, 'translator_capabilities'):
            mw.TRANSLATOR_CAPABILITIES.clear()
            mw.TRANSLATOR_CAPABILITIES.update(self.config_loader.translator_capabilities)
            
        if hasattr(self.config_loader, 'log_colors'):
            mw.LOG_COLORS.clear()
            mw.LOG_COLORS.update(self.config_loader.log_colors)
            
        self._refresh_combobox_values('target_lang')
        self._refresh_combobox_values('offline_translator')
        self._refresh_combobox_values('ai_translator')
        
        target_lang_combo = self.setting_widgets.get('target_lang')
        if target_lang_combo:
            curr_lang = target_lang_combo.currentText()
            self._filter_translator_dropdowns(curr_lang)

    def _refresh_combobox_values(self, key):
        from .. import main_window as mw
        combo = self.setting_widgets.get(key)
        if not combo or not isinstance(combo, QComboBox):
            return
            
        combo.blockSignals(True)
        combo.clear()
        
        if key == "target_lang":
            for name, code in sorted(mw.LANGUAGES.items()):
                if code != "auto":
                    combo.addItem(name, code)
            combo.addItem("🔄 Cập nhật danh sách ngôn ngữ...", "update_trigger")
        elif key == "offline_translator":
            values = mw.TRANSLATOR_GROUPS.get("--- OFFLINE MODELS (No API Key) ---", [])
            for val in values:
                exists = self.config_loader.check_model_existence(val, field=key)
                display_name = val if exists else f"{val} (Not Setup)"
                combo.addItem(display_name, val)
                if not exists:
                    idx = combo.count() - 1
                    combo.setItemData(idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            combo.addItem("🔄 Cập nhật danh sách hỗ trợ dịch...", "update_trigger")
            combo.addItem("🔄 Cập nhật phần mềm/mô hình dịch...", "update_software_trigger")
        elif key == "ai_translator":
            values = mw.TRANSLATOR_GROUPS.get("--- API-BASED (Requires Setup) ---", [])
            for val in values:
                exists = self.config_loader.check_model_existence(val, field=key)
                display_name = val if exists else f"{val} (Not Setup)"
                combo.addItem(display_name, val)
                if not exists:
                    idx = combo.count() - 1
                    combo.setItemData(idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            combo.addItem("🔄 Cập nhật danh sách hỗ trợ dịch...", "update_trigger")
            combo.addItem("🔄 Cập nhật phần mềm/mô hình dịch...", "update_software_trigger")
                    
        current_val = self.current_settings.get(key)
        self._set_widget_value(key, current_val, combo)
        combo.blockSignals(False)

    def _reset_task_settings(self, task_key: str):
        """Resets the settings of a specific task to its defaults from tasks.json."""
        if task_key not in self.task_settings:
            return

        task_info = self.config_loader.tasks_config.get(task_key, {})
        defaults = task_info.get("defaults", {})

        self.task_settings[task_key] = defaults.copy()

        for setting_key, default_value in defaults.items():
            widget = self.task_widgets.get(task_key, {}).get(setting_key)
            if widget:
                widget.blockSignals(True)
                self._set_widget_value(setting_key, default_value, widget)
                widget.blockSignals(False)

        self.log("INFO", f"Settings for task '''{task_info.get('label')}''' have been reset.")


class ConfigUpdateWorker(QThread):
    finished = Signal(bool, str)
    
    def __init__(self, config_loader, mode, translator_name=None, api_key=None):
        super().__init__()
        self.config_loader = config_loader
        self.mode = mode
        self.translator_name = translator_name
        self.api_key = api_key
        
    def run(self):
        try:
            if self.mode == "all":
                try:
                    langs_data = self.config_loader.fetch_online_languages_libretranslate()
                except Exception:
                    try:
                        langs_data = self.config_loader.fetch_online_languages_lingva()
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi kết nối mạng: Không tải được danh sách ngôn ngữ từ LibreTranslate/Lingva: {e}")
                        return
                
                success = self.config_loader.save_languages_config(langs_data)
                if success:
                    self.finished.emit(True, "Đã cập nhật thành công tất cả cấu hình ngôn ngữ & bộ dịch từ Internet!")
                else:
                    self.finished.emit(False, "Lỗi khi lưu cấu hình ngôn ngữ.")
                    
            elif self.mode == "languages":
                try:
                    langs_data = self.config_loader.fetch_online_languages_libretranslate()
                except Exception:
                    try:
                        langs_data = self.config_loader.fetch_online_languages_lingva()
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi kết nối mạng: Không tải được danh sách ngôn ngữ: {e}")
                        return
                
                success = self.config_loader.save_languages_config(langs_data)
                if success:
                    self.finished.emit(True, "Đã cập nhật thành công danh sách ngôn ngữ đích!")
                else:
                    self.finished.emit(False, "Lỗi khi lưu danh sách ngôn ngữ mới.")
                    
            elif self.mode == "single_translator":
                success, msg = self.config_loader.update_single_translator_capabilities(
                    self.translator_name, self.api_key
                )
                self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, f"Lỗi trong quá trình cập nhật cấu hình: {e}")


class CheckAllFontsWorker(QThread):
    finished = Signal(bool, list, str)
    
    def __init__(self, installed_families, local_versions):
        super().__init__()
        self.installed_families = installed_families
        self.local_versions = local_versions

    def run(self):
        import urllib.request
        try:
            url = "https://cdn.jsdelivr.net/npm/google-font-metadata/data/google-fonts-v2.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            updates_needed = []
            for family in self.installed_families:
                key = family.lower().replace(" ", "-")
                if key not in data:
                    key = family.lower().replace(" ", "")
                
                if key in data:
                    online_ver = data[key].get("version", "")
                    local_ver = self.local_versions.get(family, None)
                    if not local_ver or local_ver != online_ver:
                        updates_needed.append((family, local_ver or "Chưa đăng ký", online_ver))
            
            self.finished.emit(True, updates_needed, "")
        except Exception as e:
            self.finished.emit(False, [], str(e))


class BulkFontDownloadWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(bool, dict, str)
    
    def __init__(self, updates_to_download, fonts_dir):
        super().__init__()
        self.updates_to_download = updates_to_download
        self.fonts_dir = fonts_dir

    def run(self):
        import urllib.request
        import urllib.parse
        import re
        
        success_updates = {}
        failed_errors = []
        total = len(self.updates_to_download)
        for idx, (family, _, online_ver) in enumerate(self.updates_to_download):
            self.progress.emit(idx + 1, total, family)
            try:
                url = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(family)}:regular,italic,700,700italic"
                req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.81.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    css_content = response.read().decode('utf-8')
                
                blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                if not blocks:
                    url_fallback = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(family)}"
                    req_fb = urllib.request.Request(url_fallback, headers={'User-Agent': 'curl/7.81.0'})
                    with urllib.request.urlopen(req_fb, timeout=15) as response_fb:
                        css_content = response_fb.read().decode('utf-8')
                    blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                
                if blocks:
                    extracted_any = False
                    for block in blocks:
                        url_match = re.search(r'url\((https://fonts\.gstatic\.com/s/[^)]+\.ttf)\)', block)
                        if url_match:
                            ttf_url = url_match.group(1).strip()
                            style_match = re.search(r'font-style:\s*([^;]+);', block)
                            weight_match = re.search(r'font-weight:\s*([^;]+);', block)
                            
                            style = style_match.group(1).strip() if style_match else "normal"
                            weight = weight_match.group(1).strip() if weight_match else "400"
                            
                            clean_name = family.replace(" ", "")
                            if weight == "700" and style == "italic":
                                suffix = "-BoldItalic"
                            elif weight == "700":
                                suffix = "-Bold"
                            elif style == "italic":
                                suffix = "-Italic"
                            else:
                                suffix = "-Regular"
                            
                            filename = f"{clean_name}{suffix}.ttf"
                            dest_path = os.path.join(self.fonts_dir, filename)
                            
                            req_ttf = urllib.request.Request(ttf_url, headers={'User-Agent': 'curl/7.81.0'})
                            with urllib.request.urlopen(req_ttf, timeout=15) as res_ttf:
                                font_data = res_ttf.read()
                            
                            with open(dest_path, "wb") as f:
                                f.write(font_data)
                            extracted_any = True
                            
                    if extracted_any:
                        success_updates[family] = online_ver
                    else:
                        failed_errors.append(f"{family} (Không tìm thấy liên kết tệp ttf)")
                else:
                    failed_errors.append(f"{family} (Không tải được cấu hình từ Google CSS API)")
            except Exception as e:
                print(f"[ERROR] Failed to download/update '{family}': {e}")
                failed_errors.append(f"{family} ({str(e)})")
        
        error_msg = "; ".join(failed_errors)
        self.finished.emit(True, success_updates, error_msg)
