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
import string
import threading
import subprocess
from PySide6.QtWidgets import (
    QWidget, QComboBox, QCheckBox, QLineEdit, QButtonGroup, QMessageBox,
    QMenu, QColorDialog, QDialog, QApplication, QSlider
)
from PySide6.QtCore import Qt, Signal, QThread, QByteArray
from PySide6.QtGui import QColor
from desktop_ui.constants import *


from .widgets_helper import (
    DynamicHeightListWidget, SearchableComboBox, NoScrollComboBox,
    SearchableFontInstallDialog
)

class FontDownloadWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int, int, str)
    
    def __init__(self, font_family, fonts_dir):
        super().__init__()
        self.font_family = font_family
        self.fonts_dir = fonts_dir

    def run(self):
        import urllib.request
        import urllib.parse
        import re
        import os
        try:
            url = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(self.font_family)}:regular,italic,700,700italic"
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.81.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                css_content = response.read().decode('utf-8')
            
            blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
            if not blocks:
                url_fallback = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(self.font_family)}"
                req_fb = urllib.request.Request(url_fallback, headers={'User-Agent': 'curl/7.81.0'})
                with urllib.request.urlopen(req_fb, timeout=15) as response_fb:
                    css_content = response_fb.read().decode('utf-8')
                blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
            
            if not blocks:
                self.finished.emit(False, "Không tìm thấy cấu hình phông chữ trên Google Fonts.")
                return

            os.makedirs(self.fonts_dir, exist_ok=True)
            extracted_any = False
            
            total_blocks = len(blocks)
            
            for idx, block in enumerate(blocks):
                url_match = re.search(r'url\((https://fonts\.gstatic\.com/s/[^)]+\.ttf)\)', block)
                if url_match:
                    ttf_url = url_match.group(1).strip()
                    style_match = re.search(r'font-style:\s*([^;]+);', block)
                    weight_match = re.search(r'font-weight:\s*([^;]+);', block)
                    
                    style = style_match.group(1).strip() if style_match else "normal"
                    weight = weight_match.group(1).strip() if weight_match else "400"
                    
                    clean_name = self.font_family.replace(" ", "")
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
                    
                    self.progress.emit(idx, total_blocks, filename)
                    
                    req_ttf = urllib.request.Request(ttf_url, headers={'User-Agent': 'curl/7.81.0'})
                    with urllib.request.urlopen(req_ttf, timeout=15) as res_ttf:
                        font_data = res_ttf.read()
                    
                    with open(dest_path, "wb") as f:
                        f.write(font_data)
                    extracted_any = True
                    
                    self.progress.emit(idx + 1, total_blocks, filename)
                    
            if extracted_any:
                self.finished.emit(True, self.font_family)
            else:
                self.finished.emit(False, "Không tìm thấy tệp font phù hợp để tải về.")
        except Exception as e:
            self.finished.emit(False, str(e))


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
        """Toggles the visibility of translator settings based on Offline vs AI category."""
        category = self._get_active_translator_category()
        
        show_offline = (category == 'Offline')
        show_ai = (category == 'AI / Online')

        if 'offline_translator' in self.setting_rows:
            self.setting_rows['offline_translator'].setVisible(show_offline)

        ai_mode = self.current_settings.get('ai_mode', 'Standalone API')
        show_standalone = show_ai and (ai_mode == 'Standalone API')
        show_pool = show_ai and (ai_mode == 'Pool APIs')

        if 'ai_mode' in self.setting_rows:
            self.setting_rows['ai_mode'].setVisible(show_ai)
            
        if 'pool_name' in self.setting_rows:
            self.setting_rows['pool_name'].setVisible(show_pool)

        # Show all AI fields when AI / Online is selected
        profile_selected = self.current_settings.get('api_name', '').strip()
        has_profile = bool(profile_selected and profile_selected.lower() not in ["none", "--- select ---"])
        
        for ai_key in ['api_name', 'ai_translator', 'ai_endpoint', 'ai_model', 'ai_key', 'max_retries']:
            if ai_key in self.setting_rows:
                if ai_key == 'api_name':
                    self.setting_rows[ai_key].setVisible(show_standalone)
                else:
                    self.setting_rows[ai_key].setVisible(show_standalone and has_profile)

        # Dynamic locking for AI Endpoint
        from PySide6.QtWidgets import QLineEdit
        ai_provider = self._get_value_from_widget('ai_translator', self.setting_widgets.get('ai_translator'))
        ai_endpoint_widget = self.setting_widgets.get('ai_endpoint')
        if ai_endpoint_widget:
            entry = ai_endpoint_widget if isinstance(ai_endpoint_widget, QLineEdit) else ai_endpoint_widget.findChild(QLineEdit)
            if entry:
                if ai_provider == 'custom_openai':
                    entry.setEnabled(True)
                    entry.setReadOnly(False)
                else:
                    entry.setEnabled(False)
                    entry.setReadOnly(True)
                    ai_registry = getattr(self.config_loader, 'model_registry', {}).get('ai_translator', {})
                    if ai_provider in ai_registry:
                        default_ep = ai_registry[ai_provider].get('default_endpoint', '')
                        if default_ep:
                            entry.setText(default_ep)
                            self.current_settings['ai_endpoint'] = default_ep
                            # Force auto-save to profile
                            self._on_setting_changed('ai_endpoint')
    def _get_active_ocr_category(self) -> str:
        """Returns 'Offline' or 'AI / Online' for OCR."""
        widget = self.setting_widgets.get('ocr_category')
        if not widget:
            return 'Offline'
        val = self._get_value_from_widget('ocr_category', widget)
        return val or 'Offline'

    def _update_ocr_visibility(self):
        """Toggles the visibility of OCR/Detector settings based on Offline vs API category."""
        category = self._get_active_ocr_category()
        
        show_offline = (category == 'Offline')
        show_api = (category == 'AI / Online')

        for key in ['offline_detector', 'detection_size', 'offline_ocr']:
            if key in self.setting_rows:
                self.setting_rows[key].setVisible(show_offline)

        ocr_ai_mode = self.current_settings.get('ocr_ai_mode', 'Standalone API')
        show_standalone = show_api and (ocr_ai_mode == 'Standalone API')
        show_pool = show_api and (ocr_ai_mode == 'Pool APIs')

        if 'ocr_ai_mode' in self.setting_rows:
            self.setting_rows['ocr_ai_mode'].setVisible(show_api)

        if 'ocr_pool_name' in self.setting_rows:
            self.setting_rows['ocr_pool_name'].setVisible(show_pool)

        profile_selected = str(self.current_settings.get('ocr_api_name', '') or '').strip()
        has_profile = bool(profile_selected and profile_selected.lower() not in ["none", "--- select ---"])

        for key in ['ocr_api_name', 'api_ocr', 'ocr_api_endpoint', 'ocr_api_model', 'ocr_api_key']:
            if key in self.setting_rows:
                if key == 'ocr_api_name':
                    self.setting_rows[key].setVisible(show_standalone)
                else:
                    self.setting_rows[key].setVisible(show_standalone and has_profile)
                    
        # Dynamic locking for Endpoint
        from PySide6.QtWidgets import QLineEdit
        provider = self._get_value_from_widget('api_ocr', self.setting_widgets.get('api_ocr'))
        endpoint_widget = self.setting_widgets.get('ocr_api_endpoint')
        if endpoint_widget:
            entry = endpoint_widget if isinstance(endpoint_widget, QLineEdit) else endpoint_widget.findChild(QLineEdit)
            if entry:
                if provider == 'custom_ocr':
                    entry.setEnabled(True)
                    entry.setReadOnly(False)
                else:
                    entry.setEnabled(False)
                    entry.setReadOnly(True)
                    api_ocr_registry = self.config_loader.model_registry.get('api_ocr', {})
                    if provider in api_ocr_registry:
                        default_ep = api_ocr_registry[provider].get('default_endpoint', '')
                        if default_ep:
                            entry.setText(default_ep)
                            self.current_settings['ocr_api_endpoint'] = default_ep
                            # Force auto-save to profile
                            self._on_setting_changed('ocr_api_endpoint')

    def _update_inpainter_visibility(self):
        """Toggles the visibility of SD Base Model based on the selected Inpainter."""
        from app.core.factories import InpainterFactory, DiffusionFactory
        from PySide6.QtCore import QTimer
        
        enable_advanced_diffusion = self._get_value_from_widget('enable_advanced_diffusion', self.setting_widgets.get('enable_advanced_diffusion'))
        
        # Toggle visibility of the option menus themselves
        if 'inpainter' in self.setting_rows:
            QTimer.singleShot(50, lambda v=not enable_advanced_diffusion: self.setting_rows['inpainter'].setVisible(v))
        if 'diffusion_model' in self.setting_rows:
            QTimer.singleShot(50, lambda v=enable_advanced_diffusion: self.setting_rows['diffusion_model'].setVisible(v))
            
        show_sd_base = False
        
        if enable_advanced_diffusion:
            diffusion_model = self._get_value_from_widget('diffusion_model', self.setting_widgets.get('diffusion_model'))
            if diffusion_model:
                impl_class = DiffusionFactory.get_class(diffusion_model)
                if impl_class:
                    if getattr(impl_class, 'REQUIRES_SD_BASE_MODEL', False):
                        show_sd_base = True
                else:
                    if 'powerpaint' in str(diffusion_model).lower():
                        show_sd_base = True
        else:
            inpainter = self._get_value_from_widget('inpainter', self.setting_widgets.get('inpainter'))
            if inpainter:
                impl_class = InpainterFactory.get_class(inpainter)
                if impl_class:
                    if getattr(impl_class, 'REQUIRES_SD_BASE_MODEL', False):
                        show_sd_base = True
                else:
                    if 'powerpaint' in str(inpainter).lower():
                        show_sd_base = True
        
        if 'sd_base_model' in self.setting_rows:
            widget = self.setting_rows['sd_base_model']
            QTimer.singleShot(50, lambda v=show_sd_base: widget.setVisible(v))

    def _on_ocr_category_changed(self):
        """Handles changes in OCR category (Offline vs AI/Online)."""
        self._update_ocr_visibility()
        
    def _update_task_translator_visibility(self, context_key: str):
        """Toggles the visibility of translator settings for a specific task based on its settings."""
        if not hasattr(self, 'task_rows') or context_key not in self.task_rows:
            return
        
        settings = self.task_settings.get(context_key, {})
        rows = self.task_rows.get(context_key, {})
        
        category = settings.get('translator_category', 'Offline')
        show_offline = (category == 'Offline')
        show_ai = (category == 'AI / Online')

        if 'offline_translator' in rows:
            rows['offline_translator'].setVisible(show_offline)

        ai_mode = settings.get('ai_mode', 'Standalone API')
        show_standalone = show_ai and (ai_mode == 'Standalone API')
        show_pool = show_ai and (ai_mode == 'Pool APIs')

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

    def _on_translator_category_changed(self):
        """Handles changes in translator category (Offline vs AI)."""
        self._update_translator_visibility()
        active_name = self._get_active_translator_name()
        self._on_translator_changed(active_name)

    def _fetch_ai_models(self, button):
        """Fetches models from the configured endpoint in a background thread."""
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint'))
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key'))
        
        provider_widget = self.setting_widgets.get('ai_translator')
        ai_provider = self._get_value_from_widget('ai_translator', provider_widget)

        if not endpoint and ai_provider != 'gemini':
            self.log("WARNING", "No API Endpoint URL provided. Please enter a valid URL.")
            return

        button.setEnabled(False)
        button.setText("...")

        def thread_target():
            from app.core.api_utils import fetch_remote_ai_models
            try:
                models = fetch_remote_ai_models(endpoint, key, ai_provider)
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
            QMessageBox.warning(self, "Warning", "Failed to fetch models or no models found.")
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
        
    def _test_ai_model(self, button, combo):
        """Tests the currently selected model by sending a simple prompt."""
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint'))
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key'))
        
        provider_widget = self.setting_widgets.get('ai_translator')
        ai_provider = self._get_value_from_widget('ai_translator', provider_widget)
        
        model_name = combo.currentText()
        if not model_name or model_name == "Auto":
            QMessageBox.warning(self, "Warning", "Please select a specific model to test (not Auto).")
            return

        if not endpoint and ai_provider != 'gemini':
            self.log("WARNING", "No API Endpoint URL provided. Please enter a valid URL.")
            return

        button.setEnabled(False)
        button.setText("...")

        def thread_target():
            from app.core.api_utils import test_remote_ai_model
            success, msg = test_remote_ai_model(endpoint, key, ai_provider, model_name)
            self.test_finished_signal.emit(success, msg, button)

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_test_finished(self, success, message, button):
        button.setEnabled(True)
        button.setText("Test")
        if success:
            QMessageBox.information(self, "Test Successful", message)
        else:
            QMessageBox.critical(self, "Test Failed", message)

    def _on_fetch_finished(self, button):
        button.setEnabled(True)
        button.setText("Fetch")

    def _get_api_profiles_file_path(self) -> str:
        base_dir = os.path.join(self.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'api_profiles.yaml')

    def _load_api_profiles(self) -> dict:
        path = self._get_api_profiles_file_path()
        if os.path.exists(path):
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.load(f) or {}
                
                # Automigrate pool_profiles.yaml
                pool_path = self._get_yaml_config_path('pool_profiles.yaml')
                if os.path.exists(pool_path):
                    try:
                        with open(pool_path, 'r', encoding='utf-8') as f:
                            pool_data = yaml.load(f) or {}
                        changed = False
                        for k, v in pool_data.items():
                            if k not in data:
                                data[k] = {"type": "Pool", "service": "Translator", "fallback_list": v}
                                changed = True
                        if changed:
                            self._save_yaml_config('api_profiles.yaml', data)
                        os.rename(pool_path, pool_path + ".migrated")
                    except Exception as e:
                        print(f"[ERROR] Pool Migration failed: {e}")
                return data
            except Exception as e:
                print(f"[ERROR] Failed to load API profiles: {e}")
        
        from dotenv import load_dotenv
        load_dotenv(os.path.join(self.project_base_dir, ".env"))

        return {
            "My Custom API": {
                "group": "Standalone",
                "endpoint": "",
                "model": "Auto",
                "key": ""
            }
        }

    def _get_yaml_config_path(self, filename: str) -> str:
        import os
        base_dir = os.path.join(self.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, filename)

    def _save_yaml_config(self, filename: str, data: dict, wrap_key: str = None):
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        path = self._get_yaml_config_path(filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if wrap_key:
                    yaml.dump({wrap_key: data}, f)
                else:
                    yaml.dump(data, f)
        except Exception as e:
            print(f"[ERROR] Failed to save {filename}: {e}")

    def _save_api_profiles(self, profiles: dict):
        self._save_yaml_config('api_profiles.yaml', profiles)

    def _get_profile_mapping(self, service: str) -> dict:
        mappings = {
            "OCR": {'name': 'ocr_api_name', 'provider': 'api_ocr', 'endpoint': 'ocr_api_endpoint', 'model': 'ocr_api_model', 'key': 'ocr_api_key'},
            "Translator": {'name': 'api_name', 'provider': 'ai_translator', 'endpoint': 'ai_endpoint', 'model': 'ai_model', 'key': 'ai_key', 'max_retries': 'max_retries'},
        }
        return mappings.get(service, mappings["Translator"])

    def _save_api_profile_generic(self, service: str):
        mapping = self._get_profile_mapping(service)
        name_widget = self.setting_widgets.get(mapping['name'])
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        from PySide6.QtWidgets import QInputDialog
        profile_name, ok = QInputDialog.getText(self, f"New {service} Profile", "Enter a name for the new API Profile:")
        if not ok:
            return
            
        profile_name = profile_name.strip()
        if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
            self.log("WARNING", "Please enter a valid API Profile Name before saving.")
            return

        endpoint = self._get_value_from_widget(mapping['endpoint'], self.setting_widgets.get(mapping['endpoint'])) or ''
        
        provider = self._get_value_from_widget(mapping['provider'], self.setting_widgets.get(mapping['provider'])) or ''
            
        model = self._get_value_from_widget(mapping['model'], self.setting_widgets.get(mapping['model'])) or ''
        key = self._get_value_from_widget(mapping['key'], self.setting_widgets.get(mapping['key'])) or ''

        profiles = self._load_api_profiles()
        profiles[profile_name] = {
            "type": "Standalone",
            "service": service,
            "provider": provider,
            "endpoint": endpoint,
            "model": model,
            "key": key
        }
        self._save_api_profiles(profiles)

        filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("--- Select ---")
        combo.addItems(filtered_profiles)
        combo.setCurrentText(profile_name)
        combo.blockSignals(False)
        self.current_settings[mapping['name']] = profile_name

        self.log("SUCCESS", f"API Profile '{profile_name}' saved to local config.")

    def _delete_api_profile_generic(self, service: str):
        mapping = self._get_profile_mapping(service)
        name_widget = self.setting_widgets.get(mapping['name'])
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name or profile_name == "--- Select ---":
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa hồ sơ",
            f"Bạn có chắc chắn muốn xóa hồ sơ '{profile_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self._load_api_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            self._save_api_profiles(profiles)
            self.log("SUCCESS", f"Đã xóa hồ sơ '{profile_name}'.")

            filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]

            combo.blockSignals(True)
            combo.clear()
            combo.addItem("--- Select ---")
            combo.addItems(filtered_profiles)
            combo.setCurrentText("--- Select ---")
            combo.blockSignals(False)
            self._on_api_profile_changed_generic("--- Select ---", service)
        else:
            self.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")

    def _clear_api_widgets_generic(self, service: str):
        mapping = self._get_profile_mapping(service)
        for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
            widget = self.setting_widgets.get(key)
            if widget:
                self.current_settings[key] = ""
                self._set_widget_value(key, "", widget)

    def _on_api_profile_changed_generic(self, profile_name: str, service: str):
        profile_name = (profile_name or "").strip()
        mapping = self._get_profile_mapping(service)
        
        if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
            self.current_settings[mapping['name']] = ""
            self._clear_api_widgets_generic(service)
            update_method = getattr(self, f"_update_{service.lower()}_visibility", None)
            if update_method: update_method()
            return
            
        profiles = self._load_api_profiles()
        if profile_name in profiles:
            profile = profiles[profile_name]
            
            self._loading_api_profile = True
            try:
                for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
                    widget = self.setting_widgets.get(key)
                    if widget:
                        val = profile.get(field, '')
                        self.current_settings[key] = val
                        self._set_widget_value(key, val, widget)
            finally:
                self._loading_api_profile = False
        else:
            self.current_settings[mapping['name']] = profile_name
            self._clear_api_widgets_generic(service)
            
        update_method = getattr(self, f"_update_{service.lower()}_visibility", None)
        if update_method: update_method()


    def _get_preset_profiles_file_path(self) -> str:
        return self._get_yaml_config_path('profiles.yaml')

    def _load_preset_profiles(self) -> dict:
        import os
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        path = self._get_preset_profiles_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.load(f) or {}
            except Exception as e:
                print(f"[ERROR] Failed to load preset profiles: {e}")
        return {}

    def _save_preset_profiles(self, profiles: dict):
        self._save_yaml_config('profiles.yaml', profiles)

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
        from desktop_ui.mainwindow.pool_dialog import ManagePoolsDialog
        dialog = ManagePoolsDialog(self, service)
        if dialog.exec():
            # Dialog saved something, we need to refresh the pool selector UI
            widget_key = 'ocr_pool_name' if service == "OCR" else 'pool_name'
            pool_widget = self.setting_widgets.get(widget_key)
            if pool_widget:
                combo = pool_widget.findChild(QComboBox)
                if combo:
                    pools = self._load_pool_profiles(service)
                    current_text = combo.currentText()
                    combo.blockSignals(True)
                    combo.clear()
                    combo.addItem("--- Select ---")
                    combo.addItems(list(pools.keys()))
                    if current_text in pools:
                        combo.setCurrentText(current_text)
                    else:
                        combo.setCurrentText("--- Select ---")
                    combo.blockSignals(False)

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

            # Runtime fallback: repair any model field pointing at a deleted or
            # not-set-up model, and persist the fix so it won't recur.
            changes = self.config_loader.sweep_settings(loaded_settings)
            if changes:
                profiles[name] = copy.deepcopy(loaded_settings)
                self._save_preset_profiles(profiles)
                for k, old, new in changes:
                    self.log("WARNING", f"Model '{old}' không khả dụng -> đã chuyển '{k}' sang '{new or '(trống)'}'.")

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
        elif widget_type == "spinbox":
            from PySide6.QtWidgets import QSpinBox
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(handler)
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                button_group.buttonClicked.connect(handler)
                if key in ['translator_category', 'ai_mode']:
                    button_group.buttonClicked.connect(lambda *args: self._on_translator_category_changed())
                if key == 'ocr_category':
                    button_group.buttonClicked.connect(lambda *args: self._on_ocr_category_changed())
        elif widget_type == "api_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                service = info.get("service", "Translator")
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(lambda text, s=service: self._on_api_profile_changed_generic(text, s))
                if combo.lineEdit():
                    combo.lineEdit().returnPressed.connect(combo.showPopup)
        elif widget_type == "pool_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.activated.connect(lambda index: self._on_setting_changed('ai_model'))
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                slider.valueChanged.connect(handler)
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.editingFinished.connect(handler)

    def _on_setting_changed(self, key: str, context_key: str = None):
        """A generic handler called whenever a setting widget's value changes."""
        if context_key:
            widget = self.task_widgets[context_key].get(key)
            new_value = self._get_value_from_widget(key, widget)
            self.task_settings[context_key][key] = new_value
            print(f"[Task Settings] Updated '{context_key}.{key}' to: {new_value}")
            if key in ['translator_category', 'ai_mode', 'api_name']:
                self._update_task_translator_visibility(context_key)
        else:
            widget = self.setting_widgets.get(key)
            if key == 'translator_chain':
                new_value = self._get_translator_chain_string()
            else:
                new_value = self._get_value_from_widget(key, widget)
                
            if isinstance(widget, QComboBox):
                text = widget.currentText()
                if text in [UPDATE_LANGS_LIST, UPDATE_SUPPORTED_LANGS]:
                    self._trigger_online_config_update_from_combo(key, widget)
                    return

            self.current_settings[key] = new_value
            print(f"[Settings] Updated '{key}' to: {new_value}")

            # Also apply this change to ALL currently selected jobs in the queue
            if hasattr(self, 'queue_list_widget') and hasattr(self, 'job_queue'):
                selected_items = self.queue_list_widget.selectedItems()
                if selected_items:
                    selected_ids = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}
                    for job in self.job_queue:
                        if job.get('id') in selected_ids:
                            if 'settings' not in job:
                                job['settings'] = {}
                            job['settings'][key] = new_value

            # Auto-save changes to provider, endpoint, model, key into the currently active profile
            if key in ['ai_translator', 'ai_endpoint', 'ai_model', 'ai_key', 'max_retries', 'api_ocr', 'ocr_api_endpoint', 'ocr_api_model', 'ocr_api_key']:
                is_ocr = key.startswith('ocr_') or key == 'api_ocr'
                p_key = 'ocr_api_name' if is_ocr else 'api_name'
                profile_name = self.current_settings.get(p_key, '').strip()
                
                if profile_name and profile_name.lower() not in ["none", "--- select ---"] and not getattr(self, '_loading_api_profile', False):
                    profiles = self._load_api_profiles()
                    if profile_name in profiles:
                        if key in ['ai_translator', 'api_ocr']:
                            field_name = 'provider'
                        elif is_ocr:
                            field_name = key.replace('ocr_api_', '')
                        else:
                            field_name = key.replace('ai_', '')
                        profiles[profile_name][field_name] = new_value
                        self._save_api_profiles(profiles)
            
            if key in ['translator_category', 'ai_mode', 'ai_translator']:
                self._update_translator_visibility()
                self._update_max_length_label()

            if key in ['system_prompt_profile', 'api_name']:
                self._update_max_length_label()
                
            if key in ['ocr_category', 'ocr_ai_mode', 'api_ocr']:
                self._update_ocr_visibility()
                
            if key in ['inpainter', 'enable_advanced_diffusion', 'diffusion_model']:
                self._update_inpainter_visibility()

            if key == 'app_language':
                self.config_loader.oldsession_config["app_language"] = new_value
                self.config_loader.save_oldsession_config()
                self._rebuild_settings_tab()

    def _update_max_length_label(self):
        """Updates the label of max_request_length dynamically based on plugin MAX_CHARS and system prompt."""
        from app.core.factories import TranslatorFactory
        from app.core.translator_utils import PromptBuilder
        
        # 1. Get the current translator plugin's MAX_CHARS
        translator_name = self._get_active_translator_name()
        max_chars = -1
        try:
            translator_class = TranslatorFactory.get_class(translator_name)
            if translator_class and hasattr(translator_class, 'MAX_CHARS'):
                max_chars = translator_class.MAX_CHARS
        except Exception:
            pass
            
        # 2. Calculate system prompt length
        sys_prompt_len = 0
        sys_profile = self.current_settings.get('system_prompt_profile', 'example')
        if sys_profile and sys_profile != "None":
            project_base = getattr(self.config_loader, 'project_base_dir', "")
            if not project_base:
                import os
                project_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            builder = PromptBuilder(project_base, sys_profile)
            tgt_lang = self.current_settings.get('target_lang', 'ENG')
            sys_prompt_len = len(builder.build_prompt("auto", tgt_lang))
            
        # 3. Calculate max available length
        if max_chars > 0:
            available = max_chars - sys_prompt_len
            label_text = f"Max Request Length (Max: {available} chars):"
        else:
            label_text = "Max Request Length (Max: -1 chars):"
            
        # 4. Update the label UI
        if hasattr(self, 'setting_labels') and 'max_request_length' in self.setting_labels:
            self.setting_labels['max_request_length'].setText(label_text)

    def _on_translator_changed(self, translator_name: str):
        """Handles changes in the main translator selection."""
        if translator_name == UPDATE_SUPPORTED_LANGS:
            return
        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]
        self._update_translator_tooltip(translator_name)

    def _is_translator_supported_for_target(self, translator_name: str, target_code: str) -> bool:
        """Kiểm tra xem mô hình dịch thuật có hỗ trợ ngôn ngữ đích không."""
        from .. import main_window as mw
        from app.core.factories import TranslatorFactory
        if translator_name in ["none", "original"]:
            return True
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        if capabilities.get('__any__') == '__all__':
            return True
        for source_lang, target_langs in capabilities.items():
            if target_code in target_langs:
                return True
        return False

    def _filter_translator_dropdowns(self, target_lang_name: str, context_key: str = None):
        """Filters the offline_translator and ai_translator dropdowns based on the selected target language."""
        from .. import main_window as mw
        if not target_lang_name:
            return

        target_code = mw.LANGUAGES.get(target_lang_name)
        if not target_code:
            return

        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        if context_key:
            offline_combo = self.task_widgets.get(context_key, {}).get('offline_translator')
        else:
            offline_combo = self.setting_widgets.get('offline_translator')
            
        if offline_combo:
            current_val = offline_combo.currentData()
            offline_combo.blockSignals(True)
            offline_combo.clear()
            offline_combo.addItem("--- Select ---", "none")
            
            setup_items = []
            not_setup_items = []
            for val in self.original_offline_translators:
                supported = self._is_translator_supported_for_target(val, target_code)
                exists = self.config_loader.check_model_existence(val, field='offline_translator')
                
                label = self.config_loader.format_display_label(val, 'offline_translator')
                if not exists:
                    label += " (Not Setup)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if exists:
                    setup_items.append((val, label, not supported))
                else:
                    not_setup_items.append((val, label, not supported))
            
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            for val, label, is_unsupported in setup_items:
                offline_combo.addItem(label, val)
                if is_unsupported:
                    last_idx = offline_combo.count() - 1
                    offline_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
            for val, label, is_unsupported in not_setup_items:
                offline_combo.addItem(label, val)
                last_idx = offline_combo.count() - 1
                offline_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            is_en = self.config_loader.studio_config.get("app_language", "vi") == "en"
            update_langs_text = UPDATE_SUPPORTED_LANGS_EN if is_en else UPDATE_SUPPORTED_LANGS
            update_software_text = UPDATE_SOFTWARE_EN if is_en else UPDATE_SOFTWARE
            
            offline_combo.addItem(update_langs_text, "update_trigger")
            offline_combo.addItem(update_software_text, "update_software_trigger")
            
            restored = False
            for i in range(offline_combo.count()):
                if offline_combo.itemData(i) == current_val:
                    offline_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and offline_combo.count() > 0:
                offline_combo.setCurrentIndex(0)
            offline_combo.blockSignals(False)
            self._on_setting_changed('offline_translator', context_key)

        if context_key:
            ai_combo = self.task_widgets.get(context_key, {}).get('ai_translator')
        else:
            ai_combo = self.setting_widgets.get('ai_translator')
            
        if ai_combo:
            current_val = ai_combo.currentData()
            ai_combo.blockSignals(True)
            ai_combo.clear()
            ai_combo.addItem("--- Select ---", "none")
            setup_items = []
            not_setup_items = []
            for val in self.original_ai_translators:
                supported = self._is_translator_supported_for_target(val, target_code)
                exists = self.config_loader.check_model_existence(val, field='ai_translator')
                
                label = self.config_loader.format_display_label(val, 'ai_translator')
                if not exists:
                    label += " (Not Setup)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if exists:
                    setup_items.append((val, label, not supported))
                else:
                    not_setup_items.append((val, label, not supported))
            
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            for val, label, is_unsupported in setup_items:
                ai_combo.addItem(label, val)
                if is_unsupported:
                    last_idx = ai_combo.count() - 1
                    ai_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
            for val, label, is_unsupported in not_setup_items:
                ai_combo.addItem(label, val)
                last_idx = ai_combo.count() - 1
                ai_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            is_en = self.config_loader.studio_config.get("app_language", "vi") == "en"
            update_langs_text = UPDATE_SUPPORTED_LANGS_EN if is_en else UPDATE_SUPPORTED_LANGS
            update_software_text = UPDATE_SOFTWARE_EN if is_en else UPDATE_SOFTWARE

            ai_combo.addItem(update_langs_text, "update_trigger")
            ai_combo.addItem(update_software_text, "update_software_trigger")
            
            restored = False
            for i in range(ai_combo.count()):
                if ai_combo.itemData(i) == current_val:
                    ai_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and ai_combo.count() > 0:
                ai_combo.setCurrentIndex(0)
            ai_combo.blockSignals(False)
            self._on_setting_changed('ai_translator', context_key)

        self._update_translator_visibility()
        self._update_ocr_visibility()
        self._update_inpainter_visibility()
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

        current_val = translator_combo.currentData()
        translator_combo.blockSignals(True)
        translator_combo.clear()

        for group_name, translators in mw.TRANSLATOR_GROUPS.items():
            field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
            
            setup_items = []
            not_setup_items = []
            for t in translators:
                supported = self._is_translator_supported_for_target(t, target_code)
                exists = self.config_loader.check_model_existence(t, field=field_name)
                
                label = self.config_loader.format_display_label(t, field_name)
                if not exists:
                    label += " (Not Setup)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if exists:
                    setup_items.append((t, label, not supported))
                else:
                    not_setup_items.append((t, label, not supported))
                    
            import re
            def natural_sort_key(s):
                return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
                
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            if not setup_items and not not_setup_items:
                continue
            
            item_index = translator_combo.count()
            translator_combo.addItem(group_name)
            translator_combo.model().item(item_index).setEnabled(False)
            
            for t, label, is_unsupported in setup_items:
                translator_combo.addItem(label, t)
                if is_unsupported:
                    last_idx = translator_combo.count() - 1
                    translator_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            for t, label, is_unsupported in not_setup_items:
                translator_combo.addItem(label, t)
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
        if target_lang_name == UPDATE_LANGS_LIST:
            return
        self._filter_translator_dropdowns(target_lang_name)

    def _filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        """A centralized function to filter a given language QComboBox based on translator capabilities."""
        from .. import main_window as mw
        if not lang_combo:
            return

        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]

        from app.core.factories import TranslatorFactory
        capabilities = TranslatorFactory.get_capabilities(translator_name)
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
        lang_combo.addItem("--- Select ---", "none")
        if not supported_display_names:
            lang_combo.addItem("No Supported Targets")
            lang_combo.setEnabled(False)
        else:
            for name in sorted(supported_display_names):
                lang_combo.addItem(name, mw.LANGUAGES[name])
            lang_combo.setEnabled(True)
        lang_combo.blockSignals(False)

        if current_selection == "--- Select ---" or current_selection == "none":
            lang_combo.setCurrentIndex(0)
        elif current_selection in supported_display_names:
            lang_combo.setCurrentText(current_selection)
        else:
            lang_combo.setCurrentIndex(0)

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
                
                if widget_type == "combobox_fonts" and hasattr(self, "_style_custom_fonts_in_combobox"):
                    self._style_custom_fonts_in_combobox(combo)
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
            settings = getattr(self.config_loader, 'oldsession_config', {})
            geometry_hex = settings.get("window_geometry")
            if geometry_hex:
                self.restoreGeometry(QByteArray.fromHex(geometry_hex.encode('utf-8')))

            self.last_selected_directory = settings.get("last_directory")
            print("[INFO] Application state loaded.")
        except Exception as e:
            print(f"[WARNING] Could not load app settings: {e}")

    def _save_app_state(self):
        """Saves the current application state to the unified config."""
        if not hasattr(self.config_loader, 'oldsession_config'):
            self.config_loader.oldsession_config = {}
        self.config_loader.oldsession_config["window_geometry"] = self.saveGeometry().toHex().data().decode('utf-8')
        self.config_loader.oldsession_config["last_directory"] = getattr(self, 'last_selected_directory', None)
        
        # Save UI Session State (current settings and theme) to oldsession.yaml
        if hasattr(self.config_loader, 'oldsession_config'):
            self.config_loader.oldsession_config["current_settings"] = getattr(self, 'current_settings', {})
            if hasattr(self, 'theme_combobox'):
                self.config_loader.oldsession_config["theme"] = self.theme_combobox.currentText()
                
            if hasattr(self, 'task_settings'):
                self.config_loader.oldsession_config["task_settings"] = self.task_settings
            if hasattr(self, 'job_queue'):
                self.config_loader.oldsession_config["job_queue"] = self.job_queue
            if hasattr(self, 'history_queue'):
                self.config_loader.oldsession_config["history_queue"] = self.history_queue
                
            self.config_loader.save_oldsession_config()
            
        print("[INFO] Application state saved.")

    def _load_themes(self):
        """Scans the themes directory and populates the theme combobox."""
        self.available_themes.clear()
        themes_dir = os.path.join(self.project_base_dir, "themes")
        self.available_themes["Default Qt"] = {"name": "Default Qt", "style": {}}

        if not os.path.isdir(themes_dir):
            self.theme_combobox.addItems(sorted(self.available_themes.keys()))
            return

        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        for filename in os.listdir(themes_dir):
            if filename.endswith(".yaml"):
                try:
                    filepath = os.path.join(themes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        theme_data = yaml.load(f) or {}
                        theme_name = theme_data.get("name", filename)
                        self.available_themes[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        self.theme_combobox.addItems(sorted(self.available_themes.keys()))

    def _apply_theme(self, theme_name: str):
        """Applies the selected theme's stylesheet to the entire application."""
        if hasattr(self, 'font_scale_combobox'):
            font_size_text = self.font_scale_combobox.currentText()
        else:
            font_size_text = "100%"
        percentage = int(font_size_text.split('%')[0])
        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            qss_path = os.path.join(self.project_base_dir, "themes", "default.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
                template = string.Template(qss_content)
                minimal_style = template.safe_substitute(font_size=font_size)
                self.setStyleSheet(minimal_style)
            else:
                self.setStyleSheet(f"QWidget {{ font-size: {font_size}; }}")
            self.theme_colors = {}
            self.log("INFO", "Reverted to default Qt theme.")
            return

        theme_data = self.available_themes.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return

        colors = theme_data["style"].get("colors", {})
        self.theme_colors = colors
        
        arrow_icon_path = self._get_themed_arrow_icon_path(colors.get("text_main", "#dce4ee"), theme_name)
        
        mapping = {
            "font_size": font_size,
            "background_main": colors.get("background_main", "#2d2d2d"),
            "background_frame": colors.get("background_frame", "#2d2d2d"),
            "primary_button": colors.get("primary_button", "#3a7ebf"),
            "primary_button_hover": colors.get("primary_button_hover", "#56a9e8"),
            "slider_groove": colors.get("slider_groove", "#242424"),
            "slider_handle": colors.get("slider_handle", "#3a7ebf"),
            "text_main": colors.get("text_main", "#dce4ee"),
            "border": colors.get("border", "#555555"),
            "accent": colors.get("accent", "#4a9fcf"),
            "arrow_icon_path": arrow_icon_path
        }

        qss_path = os.path.join(self.project_base_dir, "themes", "template.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
            template = string.Template(qss_content)
            style_sheet = template.safe_substitute(mapping)
            self.setStyleSheet(style_sheet)
        
        self.log("INFO", f"Theme '''{theme_name}''' applied successfully.")

    def _show_queue_context_menu(self, position):
        """Creates and shows the context menu for the queue list."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        
        resume_action = menu.addAction("▶️ Resume (Bỏ qua file đã hoàn thành)")
        resume_action.triggered.connect(self._resume_selected_jobs)
        
        restart_action = menu.addAction("🔄 Restart (Dịch lại từ đầu)")
        restart_action.triggered.connect(self._restart_selected_jobs)

        menu.addSeparator()
        duplicate_action = menu.addAction("➕ Duplicate Job (as new task)")
        duplicate_action.triggered.connect(self._duplicate_selected_jobs)

        remove_action = menu.addAction("🗑️ Remove from Queue")
        remove_action.triggered.connect(self._remove_selected_jobs_from_queue)

        menu.exec(self.queue_list_widget.mapToGlobal(position))

    def _resume_selected_jobs(self):
        """Starts the pipeline for selected jobs, skipping existing output files."""
        self._start_pipeline_thread()
        
    def _restart_selected_jobs(self):
        """Clears previous output for selected jobs and restarts."""
        import shutil
        selected_items = self.queue_list_widget.selectedItems()
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job = next((j for j in self.job_queue if j['id'] == job_id), None)
            if job:
                out_path = job.get('output_path', '')
                if os.path.exists(out_path):
                    try:
                        shutil.rmtree(out_path)
                    except Exception as e:
                        print(f"Lỗi xóa output_path {out_path}: {e}")
        self._start_pipeline_thread()

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
        for folder in ["fonts", os.path.join(".config", "configs", "fonts")]:
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
        
        metadata_url = self.config_loader.global_settings.get("resources", {}).get(
            "google_font_metadata", 
            "https://cdn.jsdelivr.net/npm/google-font-metadata/data/google-fonts-v2.json"
        )
        
        class SingleVersionFetchWorker(QThread):
            done = Signal(str)
            def __init__(self, url):
                super().__init__()
                self.url = url
            def run(self):
                import urllib.request
                try:
                    req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
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
        
        def on_done(version):
            if version:
                versions = self.config_loader.oldsession_config.setdefault("font_versions", {})
                versions[font_family] = version
                self.config_loader.save_oldsession_config()
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

        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt
        progress_dlg = QProgressDialog(f"Đang chuẩn bị tải {google_family}...", "Hủy", 0, 100, self)
        progress_dlg.setWindowTitle("Cập nhật Phông Chữ")
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()

        self._font_worker = FontDownloadWorker(google_family, fonts_dir)
        progress_dlg.canceled.connect(self._font_worker.terminate)

        def on_progress(current, total, filename):
            progress_dlg.setMaximum(total)
            progress_dlg.setValue(current)
            progress_dlg.setLabelText(f"Đang tải: {filename} ({current}/{total})")

        self._font_worker.progress.connect(on_progress)

        def on_finished(success, message_or_family):
            progress_dlg.setValue(progress_dlg.maximum())
            progress_dlg.close()
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
                main_font_combo.addItem(UPDATE_ALL_FONTS)
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

        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt
        progress_dlg = QProgressDialog(f"Đang chuẩn bị tải {font_family}...", "Hủy", 0, 100, self)
        progress_dlg.setWindowTitle("Cài đặt Phông Chữ")
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()

        self._font_worker = FontDownloadWorker(font_family, fonts_dir)
        progress_dlg.canceled.connect(self._font_worker.terminate)

        def on_progress(current, total, filename):
            progress_dlg.setMaximum(total)
            progress_dlg.setValue(current)
            progress_dlg.setLabelText(f"Đang tải: {filename} ({current}/{total})")

        self._font_worker.progress.connect(on_progress)
        
        def on_finished(success, message_or_family):
            progress_dlg.setValue(progress_dlg.maximum())
            progress_dlg.close()
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
                main_font_combo.addItem(UPDATE_ALL_FONTS)
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
        
        metadata_url = self.config_loader.global_settings.get("resources", {}).get(
            "google_font_metadata", 
            "https://cdn.jsdelivr.net/npm/google-font-metadata/data/google-fonts-v2.json"
        )
        self._check_worker = CheckAllFontsWorker(installed_families, local_versions, metadata_url)
        
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
        
        css_url = self.config_loader.global_settings.get("resources", {}).get(
            "google_font_css", 
            "https://fonts.googleapis.com/css?family="
        )
        self._bulk_worker = BulkFontDownloadWorker(updates, fonts_dir, css_url)
        progress.canceled.connect(self._bulk_worker.terminate)
        
        def on_progress(current, total, family):
            progress.setValue(current - 1)
            progress.setLabelText(f"Đang tải ({current}/{total}): {family}...")
            
        def on_finished(success, success_updates, error_msg):
            progress.setValue(len(updates))
            progress.close()
            main_font_combo.setEnabled(True)
            
            if success_updates:
                versions = self.config_loader.oldsession_config.setdefault("font_versions", {})
                for fam, ver in success_updates.items():
                    versions[fam] = ver
                self.config_loader.save_oldsession_config()
                
                for fam in success_updates.keys():
                    self._save_font_version_from_online_metadata(fam)
                
                self.log("SUCCESS", f"Đã cập nhật thành công {len(success_updates)} phông chữ!")
                self._build_font_map()
                font_names = list(self.font_map.keys())
                
                main_font_combo.blockSignals(True)
                main_font_combo.clear()
                main_font_combo.addItems(font_names)
                main_font_combo.addItem("📥 Install New Font...")
                main_font_combo.addItem(UPDATE_ALL_FONTS)
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


    def _update_dynamic_btns(self, key: str):
        if not hasattr(self, '_dynamic_btns_map') or key not in self._dynamic_btns_map:
            return
            
        data = self._dynamic_btns_map[key]
        combo = data['combo']
        btn_tick = data['tick']
        btn_download = data['download']
        btn_search = data['search']
        btn_delete = data['delete']
        
        # Hide all first
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
                # Check if it's a store font or external font
                installed_fonts = getattr(self, '_get_installed_google_fonts', lambda: lambda: {})()
                if current_text in installed_fonts:
                    btn_download.show()
                    btn_download.setToolTip(f"Cập nhật {current_text}")
                else:
                    btn_search.show()
                    btn_search.setToolTip(f"Tìm font thay thế cho {current_text} trên Google Fonts")
                btn_delete.show()
                btn_delete.setToolTip(f"Xóa/Gỡ cài đặt {current_text}")
        else:
            if current_data in ["update_all_software_trigger", "update_trigger"]:
                btn_tick.show()
                btn_tick.setToolTip("Xác nhận Thực thi")
            else:
                btn_download.show()
                btn_download.setToolTip(f"Tải/Cập nhật mô hình {current_text}")
                btn_delete.show()
                btn_delete.setToolTip(f"Xóa mô hình {current_text}")

    def _on_dynamic_btn_clicked(self, key: str, action: str):
        if not hasattr(self, '_dynamic_btns_map') or key not in self._dynamic_btns_map:
            return
        combo = self._dynamic_btns_map[key]['combo']
        current_data = combo.itemData(combo.currentIndex())
        current_text = combo.currentText()
        
        if action == 'tick':
            if current_data == "update_all_software_trigger":
                self._trigger_all_models_software_update(key)
            elif current_data == "update_trigger":
                if key == "target_lang":
                    self._trigger_online_config_update("target_lang")
                elif key in ["offline_translator", "ai_translator"]:
                    self._trigger_all_configs_update()
            elif current_text == UPDATE_ALL_FONTS:
                self._check_and_update_all_fonts(combo)
            elif current_text == INSTALL_NEW_FONT:
                self._prompt_font_install(combo)
                
        elif action == 'download':
            if key == 'font_family':
                self._force_update_current_font(combo)
            else:
                self._trigger_model_software_update(key)
                
        elif action == 'search':
            if key == 'font_family':
                if current_text != INSTALL_NEW_FONT:
                    self._find_similar_font(combo)
                    
        elif action == 'delete':
            if key == 'font_family':
                self._delete_font(current_text)
            else:
                self._delete_model_software(key, current_data)

    def _delete_font(self, font_name: str):
        from PySide6.QtWidgets import QMessageBox
        import os, shutil
        
        if not font_name or font_name == "Sans-serif" or font_name == "No fonts found in /fonts folder":
            return
            
        reply = QMessageBox.question(self, "Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa Font '{font_name}' không?\\nHành động này sẽ xóa file khỏi hệ thống.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        fonts_dir = os.path.join(self.project_base_dir, "fonts")
        deleted = False
        
        for filename in os.listdir(fonts_dir):
            if filename.endswith(".ttf") and font_name.replace(" ", "") in filename:
                os.remove(os.path.join(fonts_dir, filename))
                deleted = True
                
        if deleted:
            QMessageBox.information(self, "Thành công", f"Đã xóa font '{font_name}'.")
            self._build_font_map()
            
            # Remove version from config
            local_versions = self.config_loader.oldsession_config.get("font_versions", {})
            if font_name in local_versions:
                del local_versions[font_name]
                self.config_loader.save_oldsession_config()
                
            combo = self._dynamic_btns_map['font_family']['combo']
            font_names = list(self.font_map.keys())
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(font_names)
            combo.addItem(INSTALL_NEW_FONT)
            combo.addItem(UPDATE_ALL_FONTS)
            self._style_custom_fonts_in_combobox(combo)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            self._update_dynamic_btns('font_family')
        else:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file font để xóa.")

    def _delete_model_software(self, key: str, model_name: str):
        from PySide6.QtWidgets import QMessageBox
        import os, shutil, json
        
        if not model_name or model_name in ["none", "original"]:
            return
            
        reply = QMessageBox.question(self, "Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa mô hình '{model_name}' không?\\nFile tải về sẽ bị gỡ bỏ, bạn sẽ phải tải lại nếu muốn dùng.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        rule = self.config_loader._DEFAULT_CHECKS.get(key, {}).get(model_name, {})
        check_file_path = rule.get("check_file", "")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if check_file_path:
            model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir, ignore_errors=True)
                
        # Remove from local_versions
        config_dir = os.path.join(base_dir, ".config", "models")
        local_versions_file = os.path.join(config_dir, "local_versions.yaml")
        if os.path.exists(local_versions_file):
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False
            with open(local_versions_file, "r", encoding="utf-8") as lf:
                local_versions = yaml.load(lf)
            if model_name in local_versions:
                del local_versions[model_name]
                with open(local_versions_file, "w", encoding="utf-8") as lf:
                    yaml.dump(local_versions, lf)
                    
        QMessageBox.information(self, "Thành công", f"Đã xóa mô hình '{model_name}'.")
        if hasattr(self, '_refresh_combobox_values'):
            self._refresh_combobox_values(key)
        self._update_dynamic_btns(key)

    def _trigger_all_models_software_update(self, key: str):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Cập nhật Hàng loạt", f"Bạn có muốn tự động tải và cập nhật TẤT CẢ mô hình thuộc nhóm '{key}' không?\\nQuá trình này có thể tốn nhiều dung lượng và thời gian.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Simplified bulk update: just show a dialog saying it's queued (since full implementation is too complex for this script, we'll implement a basic one or mock it)
        # For now, we'll just loop through and call _trigger_model_software_update sequentially or tell user to do one by one.
        info_title = "In Development" if is_en else "Đang phát triển"
        info_msg = "Bulk download feature will be implemented in a future update. Please download each model individually for now." if is_en else "Tính năng tải hàng loạt sẽ được triển khai trong bản cập nhật sau. Vui lòng tải từng mô hình ở hiện tại."
        QMessageBox.information(self, info_title, info_msg)

    def _trigger_model_software_update(self, key: str):
        """Triggers a background mock process to simulate updating the software/model weights."""
        combo = self.setting_widgets.get(key)
        if not combo:
            return
        model_name = combo.itemData(combo.currentIndex())
        if not model_name or model_name in ["none", "original"]:
            QMessageBox.information(self, "Thông tin", f"Bộ dịch '''{model_name}''' không hỗ trợ cập nhật phần mềm.")
            return
            
        source_url = getattr(self.config_loader, "model_source_map", {}).get(model_name)
        if not source_url:
            if model_name.startswith("tesseract_"):
                lang = model_name.replace("tesseract_", "")
                tess_packages = ["tesseract-ocr"]
                if lang == "mixed" or lang == "all_horizontal":
                    tess_packages.extend(["tesseract-ocr-jpn", "tesseract-ocr-jpn-vert", "tesseract-ocr-chi-sim", "tesseract-ocr-chi-sim-vert", "tesseract-ocr-chi-tra", "tesseract-ocr-chi-tra-vert", "tesseract-ocr-kor", "tesseract-ocr-kor-vert"])
                else:
                    tess_lang = lang.replace("_", "-")
                    tess_packages.append(f"tesseract-ocr-{tess_lang}")
                
                cmd = f"sudo apt-get install {' '.join(tess_packages)}"
                
                msg = QMessageBox(self)
                msg.setWindowTitle("Hướng dẫn cài đặt Tesseract")
                msg.setText(f"Mô hình '{model_name}' yêu cầu phần mềm hệ thống Tesseract OCR.\n\nVui lòng copy câu lệnh sau và dán vào Terminal để cài đặt:")
                msg.setDetailedText(cmd)
                msg.setIcon(QMessageBox.Icon.Information)
                
                copy_btn = msg.addButton("Copy Lệnh", QMessageBox.ButtonRole.ActionRole)
                close_btn = msg.addButton("Đóng", QMessageBox.ButtonRole.RejectRole)
                
                msg.exec()
                
                if msg.clickedButton() == copy_btn:
                    from PyQt6.QtGui import QGuiApplication
                    clipboard = QGuiApplication.clipboard()
                    if clipboard:
                        clipboard.setText(cmd)
                        QMessageBox.information(self, "Thành công", "Đã copy câu lệnh vào khay nhớ tạm!")
            else:
                QMessageBox.information(self, "Thông tin", f"Mô hình '{model_name}' không hỗ trợ tính năng tự động tải dữ liệu qua giao diện (có thể là API hoặc phần mềm hệ thống).")
            return

        reply = QMessageBox.question(
            self,
            "Cập nhật Bộ dịch",
            f"Bạn có muốn kiểm tra và tải/cập nhật phiên bản phần mềm hoặc tệp mô hình mới nhất của bộ dịch '''{model_name}''' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.log("INFO", f"Đang kiểm tra cập nhật phần mềm/mô hình cho bộ dịch: {model_name}...")
        
        for k in getattr(self, '_dynamic_btns_map', {}).keys():
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        # Lấy thông tin đường dẫn đích dựa vào cấu hình
        rule = self.config_loader._DEFAULT_CHECKS.get(key, {}).get(model_name, {})
        check_file_path = rule.get("check_file", "")

        class TranslatorSoftwareUpdateWorker(QThread):
            finished = Signal(bool, str)
            progress = Signal(int, str)
            
            def run(self):
                import urllib.request
                import urllib.error
                import json
                import os
                from ruamel.yaml import YAML
                yaml = YAML()
                yaml.preserve_quotes = True
                yaml.default_flow_style = False
                
                try:
                    self.progress.emit(10, f"Đang tải cấu hình nguồn của {model_name}...")
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    config_dir = os.path.join(base_dir, ".config", "models")
                    registry_file = os.path.join(config_dir, "model_registry.yaml")
                    local_versions_file = os.path.join(config_dir, "local_versions.yaml")
                    
                    if model_name in ["sd_1_5", "sd_nsfw"]:
                        try:
                            from huggingface_hub import snapshot_download
                            repo_id = "runwayml/stable-diffusion-v1-5" if model_name == "sd_1_5" else "Kernel/sd-nsfw"
                            self.progress.emit(30, f"Đang đồng bộ Base Model từ {repo_id}...")
                            
                            snapshot_download(
                                repo_id=repo_id, 
                                allow_patterns=[
                                    "*.json", 
                                    "*.txt", 
                                    "unet/*.safetensors", 
                                    "vae/*.safetensors", 
                                    "text_encoder/*.safetensors", 
                                    "tokenizer/*", 
                                    "scheduler/*", 
                                    "feature_extractor/*", 
                                    "safety_checker/*.safetensors"
                                ],
                                resume_download=True
                            )
                            
                            # Mark as completed
                            local_versions = {}
                            if os.path.exists(local_versions_file):
                                with open(local_versions_file, "r", encoding="utf-8") as lf:
                                    local_versions = yaml.load(lf) or {}
                            
                            local_versions[model_name] = "hf_latest"
                            with open(local_versions_file, "w", encoding="utf-8") as lf:
                                yaml.dump(local_versions, lf)
                                
                            self.finished.emit(True, f"Đã tải xong Base Model: {model_name}.")
                            return
                        except Exception as e:
                            self.finished.emit(False, f"Lỗi khi tải Base Model: {e}")
                            return
                    
                    if not os.path.exists(registry_file):
                        self.finished.emit(False, "Không tìm thấy file cấu hình model_registry.yaml.")
                        return
                        
                    with open(registry_file, "r", encoding="utf-8") as sf:
                        registry = yaml.load(sf)
                        
                    url = None
                    if registry and "fields" in registry:
                        for field_name, items in registry["fields"].items():
                            for item in items:
                                if item and isinstance(item, dict) and item.get("key") == model_name:
                                    url = item.get("source")
                                    break
                            if url: break
                            
                    if not url:
                        self.finished.emit(False, f"Không tìm thấy cấu hình nguồn tải (thuộc tính 'source') cho '{model_name}' trong model_registry.yaml.")
                        return
                    
                    self.progress.emit(30, "Đang kiểm tra kết nối nguồn tải...")
                    
                    is_direct_archive = False
                    is_direct_file = False
                    is_huggingface = False
                    
                    if url.startswith('hf://'):
                        is_huggingface = True
                        hf_url_parts = url[5:].split('@', 1)
                        repo_id = hf_url_parts[0]
                        hf_specific_file = hf_url_parts[1] if len(hf_url_parts) > 1 else None
                        latest_version = "hf_latest"
                        zipball_url = ""
                    elif url.lower().endswith(('.zip', '.tar.gz', '.tar')):
                        is_direct_archive = True
                        latest_version = "latest_direct"
                        zipball_url = url
                    elif url.lower().endswith(('.onnx', '.pth', '.ckpt', '.bin', '.pt')):
                        is_direct_file = True
                        latest_version = "latest_direct"
                        file_url = url
                        zipball_url = ""
                    else:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        try:
                            with urllib.request.urlopen(req, timeout=10) as response:
                                data = json.loads(response.read().decode('utf-8'))
                                latest_version = data.get("tag_name", "unknown")
                                zipball_url = data.get("zipball_url", "")
                        except Exception as e:
                            self.finished.emit(False, f"Lỗi khi kết nối đến nguồn tải (API): {e}")
                            return
                        
                    self.progress.emit(50, f"Phiên bản mới nhất trên máy chủ: {latest_version}. Đang kiểm tra cục bộ...")
                    
                    local_versions = {}
                    if os.path.exists(local_versions_file):
                        from ruamel.yaml import YAML
                        yaml = YAML()
                        yaml.preserve_quotes = True
                        yaml.default_flow_style = False
                        with open(local_versions_file, "r", encoding="utf-8") as lf:
                            local_versions = yaml.load(lf)
                            
                    current_version = local_versions.get(model_name, "none")
                    
                    # Force update if check file does not exist, even if version matches
                    needs_update = True
                    if current_version == latest_version:
                        if check_file_path:
                            full_check_path = os.path.join(base_dir, check_file_path)
                            if os.path.exists(full_check_path):
                                needs_update = False
                        else:
                            needs_update = False
                            
                    if not needs_update:
                        self.progress.emit(100, "Hoàn tất")
                        self.finished.emit(True, f"Bộ dịch '{model_name}' đã ở phiên bản mới nhất ({current_version}) và đã được cài đặt. Không cần cập nhật.")
                        return
                        
                    self.progress.emit(70, f"Đang tiến hành lấy danh sách file từ {url}...")
                    
                    # Thực sự tải file
                    if is_huggingface:
                        try:
                            if check_file_path:
                                model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
                            else:
                                model_dir = os.path.join(base_dir, "models", "Offline Translator", model_name)
                            os.makedirs(model_dir, exist_ok=True)
                            
                            hf_endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
                            tree_url = f"{hf_endpoint}/api/models/{repo_id}/tree/main?recursive=True"
                            req = urllib.request.Request(tree_url, headers={'User-Agent': 'Mozilla/5.0'})
                            
                            with urllib.request.urlopen(req, timeout=15) as response:
                                files_data = json.loads(response.read().decode('utf-8'))
                                
                            target_files = []
                            # Pre-calculate safetensors paths to avoid downloading .bin when safetensors exist
                            safetensors_paths = {item.get("path", "") for item in files_data if item.get("path", "").endswith(".safetensors")}
                            
                            for item in files_data:
                                if item.get("type") == "file":
                                    path = item.get("path", "")
                                    if hf_specific_file and path != hf_specific_file:
                                        continue
                                    ext = os.path.splitext(path)[1].lower()
                                    if ext in [".msgpack", ".h5", ".ot", ".md"] or path.startswith("."):
                                        continue
                                    if ext == ".bin":
                                        safetensors_equivalent = path[:-4] + ".safetensors"
                                        if safetensors_equivalent in safetensors_paths:
                                            continue # skip .bin if .safetensors exists
                                    target_files.append(item)
                                        
                            total_files = len(target_files)
                            if total_files == 0:
                                self.finished.emit(False, f"Không tìm thấy file hợp lệ nào trong repository {repo_id}")
                                return
                                
                            for idx, item in enumerate(target_files):
                                path = item.get("path")
                                size = item.get("size", 0)
                                import urllib.parse
                                hf_endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
                                file_url = f"{hf_endpoint}/{repo_id}/resolve/main/{urllib.parse.quote(path)}"
                                local_path = os.path.join(model_dir, path)
                                
                                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                                self.progress.emit(70 + int((idx/total_files)*25), f"Đang tải {path} ({idx+1}/{total_files})...")
                                
                                req_file = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(req_file, timeout=60) as resp:
                                    with open(local_path, "wb") as f:
                                        downloaded = 0
                                        chunk_size = 1024 * 1024
                                        while True:
                                            chunk = resp.read(chunk_size)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                            downloaded += len(chunk)
                                            if size > 0 and downloaded % (2 * 1024 * 1024) < chunk_size:
                                                percent = int((downloaded/size)*100)
                                                self.progress.emit(70 + int((idx/total_files)*25), f"Đang tải {path} ({idx+1}/{total_files}) - {percent}%")
                                                
                        except Exception as e:
                            self.finished.emit(False, f"Lỗi khi tải từ HuggingFace: {e}")
                            return
                            
                    elif is_direct_file:
                        try:
                            self.progress.emit(70, f"Đang tiến hành tải file từ {file_url}...")
                            req_file = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req_file, timeout=600) as response:
                                total_size = int(response.info().get('Content-Length', -1))
                                
                                if check_file_path:
                                    model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
                                    local_path = os.path.join(base_dir, check_file_path)
                                else:
                                    model_dir = os.path.join(base_dir, "models", "Unknown", model_name)
                                    import urllib.parse
                                    filename = os.path.basename(urllib.parse.urlparse(file_url).path)
                                    if not filename: filename = "model.bin"
                                    local_path = os.path.join(model_dir, filename)
                                    
                                os.makedirs(model_dir, exist_ok=True)
                                
                                chunk_size = 1024 * 1024
                                downloaded = 0
                                
                                with open(local_path, "wb") as f:
                                    while True:
                                        chunk = response.read(chunk_size)
                                        if not chunk:
                                            break
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size > 0:
                                            progress_percent = 70 + int((downloaded / total_size) * 20)
                                            if downloaded % (2 * 1024 * 1024) < chunk_size:
                                                self.progress.emit(progress_percent, f"Đang tải: {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB...")
                        except Exception as e:
                            self.finished.emit(False, f"Lỗi khi tải trực tiếp: {e}")
                            return
                            
                    elif zipball_url:
                        try:
                            self.progress.emit(70, f"Đang tiến hành tải dữ liệu từ {zipball_url}...")
                            req_zip = urllib.request.Request(zipball_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req_zip, timeout=600) as response:
                                import zipfile, tarfile, shutil, tempfile
                                
                                total_size = int(response.info().get('Content-Length', -1))
                                fd, temp_path = tempfile.mkstemp(suffix=".zip")
                                os.close(fd)
                                
                                chunk_size = 1024 * 1024 # 1MB chunks
                                downloaded = 0
                                
                                with open(temp_path, "wb") as f:
                                    while True:
                                        chunk = response.read(chunk_size)
                                        if not chunk:
                                            break
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        
                                        if total_size > 0:
                                            # Scale progress between 70% and 90%
                                            progress_percent = 70 + int((downloaded / total_size) * 20)
                                            # Update every ~2MB to avoid UI freezing
                                            if downloaded % (2 * 1024 * 1024) < chunk_size:
                                                self.progress.emit(progress_percent, f"Đang tải: {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB...")
                                
                                self.progress.emit(90, "Đang giải nén dữ liệu...")
                                
                                # Tạo thư mục nếu chưa có
                                if check_file_path:
                                    model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
                                else:
                                    model_dir = os.path.join(base_dir, "models", "Unknown", model_name)
                                os.makedirs(model_dir, exist_ok=True)
                                
                                if zipball_url.lower().endswith('.tar.gz'):
                                    with tarfile.open(temp_path, mode="r:gz") as tar_ref:
                                        tar_ref.extractall(model_dir)
                                else:
                                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                                        zip_ref.extractall(model_dir)
                                        
                                os.remove(temp_path)
                                        
                                # Xử lý thư mục rỗng thừa (Smart Extraction/Flatten directory)
                                items = os.listdir(model_dir)
                                if len(items) == 1:
                                    single_item_path = os.path.join(model_dir, items[0])
                                    if os.path.isdir(single_item_path):
                                        for sub_item in os.listdir(single_item_path):
                                            shutil.move(os.path.join(single_item_path, sub_item), os.path.join(model_dir, sub_item))
                                        os.rmdir(single_item_path)

                        except Exception as e:
                            self.finished.emit(False, f"Lỗi khi tải hoặc giải nén mã nguồn: {e}")
                            return
                    else:
                        self.finished.emit(False, "Không tìm thấy đường dẫn tải zipball_url.")
                        return
                    

                    # Update local version
                    local_versions[model_name] = latest_version
                    with open(local_versions_file, "w", encoding="utf-8") as lf:
                        yaml.dump(local_versions, lf)
                        
                    # Create models folder based on captured config
                    if check_file_path:
                        model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
                    else:
                        model_dir = os.path.join(base_dir, "models", "Unknown", model_name)
                        
                    os.makedirs(model_dir, exist_ok=True)
                    
                    self.progress.emit(100, "Tải Source Code và cài đặt thành công!")
                    self.finished.emit(True, f"Đã tải Source Code và cài đặt thành công mô hình '{model_name}' lên phiên bản {latest_version}!")
                except Exception as e:
                    self.finished.emit(False, f"Lỗi không xác định: {str(e)}")


        from PySide6.QtWidgets import QProgressDialog
        progress_dlg = QProgressDialog(f"Đang kiểm tra cập nhật cho {model_name}...", "Hủy", 0, 100, self)
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
            for k in getattr(self, '_dynamic_btns_map', {}).keys():
                w = self.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)
            if success:
                self.log("SUCCESS", message)
                QMessageBox.information(self, "Cập nhật Hoàn tất", message)
                # Tự động làm mới UI để xóa chữ (Not Setup)
                if hasattr(self, '_refresh_combobox_values'):
                    self._refresh_combobox_values('offline_translator')
                    self._refresh_combobox_values('ai_translator')
                    self._refresh_combobox_values(key)
            else:
                self.log("ERROR", message)
                QMessageBox.warning(self, "Cập nhật Thất bại", message)
            del self._software_worker

        self._software_worker.finished.connect(on_finished, Qt.ConnectionType.QueuedConnection)
        self._software_worker.progress.connect(on_progress, Qt.ConnectionType.QueuedConnection)
        self._software_worker.start()

    def _trigger_online_config_update_from_combo(self, key: str, combo: QComboBox):
        """(Disabled) Logic is now handled by _on_dynamic_btn_clicked."""
        pass

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

        else:
            return

        self._config_update_active = True
        
        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        self._config_worker = ConfigUpdateWorker(self.config_loader, mode, translator_name, api_key)

        self._config_worker.finished.connect(self._handle_config_update_finished)
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

        self._config_worker.finished.connect(self._handle_config_update_finished)
        self._config_worker.start()

    def _handle_config_update_finished(self, success, message):
        self._config_update_active = False
        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.setting_widgets.get(k)
            if w:
                w.setEnabled(True)
        
        if success:
            self.log("SUCCESS", message)
            self._reload_dynamic_configurations()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Cập nhật Thành công", message)
        else:
            self.log("ERROR", message)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Cập nhật Thất bại", message)
            
        if hasattr(self, '_config_worker'):
            del self._config_worker

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
        mw.TRANSLATOR_GROUPS[CAT_OFFLINE_MODELS] = offline_list
        mw.TRANSLATOR_GROUPS[CAT_API_BASED] = api_list
        mw.TRANSLATOR_GROUPS[CAT_OTHER_ACTIONS] = other_list
        
        self.original_offline_translators = list(offline_list)
        self.original_ai_translators = list(api_list)
        

            
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
            combo.addItem(UPDATE_LANGS_LIST, "update_trigger")
        elif key in self.config_loader.all_model_fields:
            if key not in ["offline_translator", "ai_translator", "api_ocr"]:
                combo.addItem("--- Select ---", "none")
                
            values_data = self.config_loader.full_registry.get("fields", {}).get(key, [])
            values = [item.get("key") for item in values_data if item.get("key") and item.get("key") != "none"]
            
            supports_langs = key in ["offline_translator", "ai_translator"]
            has_any_check_file = any(self.config_loader._DEFAULT_CHECKS.get(key, {}).get(v, {}).get("check_file") for v in values)

            for val in values:
                exists = self.config_loader.check_model_existence(val, field=key)
                display_name = self.config_loader.format_display_label(val, key)
                if not exists:
                    display_name = f"{display_name} (Not Setup)"
                combo.addItem(display_name, val)
                if not exists:
                    idx = combo.count() - 1
                    combo.setItemData(idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            
            if supports_langs:
                combo.addItem(UPDATE_SUPPORTED_LANGS, "update_trigger")
                
            if has_any_check_file:
                if key in ["offline_translator", "ai_translator"]:
                    combo.addItem(UPDATE_SOFTWARE, "update_software_trigger")
                else:
                    is_en = self.current_settings.get('app_language', 'English') in ['English', 'en', 'ENG']
                    ui_map = getattr(self.config_loader, 'ui_map', {})
                    labels = ui_map.get("labels", {})
                    localized_key = labels.get(key, key.replace("_", " ").title())
                    update_all_key_text = f"📥 Update ALL {localized_key} models..." if is_en else f"📥 Cập nhật TẤT CẢ mô hình {localized_key}..."
                    combo.addItem(update_all_key_text, "update_all_software_trigger")
                    
        current_val = self.current_settings.get(key)
        self._set_widget_value(key, current_val, combo)
        combo.blockSignals(False)
    def _export_detector_image(self):
        """Exports the detector image."""
        if not hasattr(self, 'current_test_output_dir') or not self.current_test_output_dir:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        import os, shutil
        source_file = os.path.join(self.current_test_output_dir, "test_detector.png")
        if not os.path.exists(source_file):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "Detector result image not found.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Detector Image", "detector_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Detector image exported successfully.")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export image: {str(e)}")

    def _export_ocr_data(self):
        """Exports the OCR data to a CSV file."""
        if not hasattr(self, 'current_test_output_dir') or not self.current_test_output_dir:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        import os, json, csv
        source_file = os.path.join(self.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "OCR data not found.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Export OCR Data", "ocr_data.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                bboxes = data.get("bboxes", [])
                original_texts = data.get("original_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["BBox", "Original Text"])
                    for i in range(max(len(bboxes), len(original_texts))):
                        box = str(bboxes[i]) if i < len(bboxes) else ""
                        text = original_texts[i] if i < len(original_texts) else ""
                        writer.writerow([box, text])
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "OCR data exported successfully.")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export OCR data: {str(e)}")

    def _export_translator_data(self):
        """Exports the translated text data to a CSV file."""
        if not hasattr(self, 'current_test_output_dir') or not self.current_test_output_dir:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        import os, json, csv
        source_file = os.path.join(self.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "Translation data not found.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Translated Text", "translated_text.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                original_texts = data.get("original_texts", [])
                translated_texts = data.get("translated_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Original Text", "Translated Text"])
                    for i in range(max(len(original_texts), len(translated_texts))):
                        orig = original_texts[i] if i < len(original_texts) else ""
                        trans = translated_texts[i] if i < len(translated_texts) else ""
                        writer.writerow([orig, trans])
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Translated text exported successfully.")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export translated text: {str(e)}")

    def _export_inpainter_image(self):
        """Exports the inpainted image."""
        if not hasattr(self, 'current_test_output_dir') or not self.current_test_output_dir:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        import os, shutil
        source_file = os.path.join(self.current_test_output_dir, "test_inpainter.png")
        if not os.path.exists(source_file):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "Inpainter result image not found.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Inpainted Image", "inpainter_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Inpainted image exported successfully.")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export image: {str(e)}")

    def _export_render_image(self):
        """Exports the final rendered image."""
        if not hasattr(self, 'current_test_output_dir') or not self.current_test_output_dir:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        import os, shutil
        if not hasattr(self, 'test_image_path') or not self.test_image_path:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "No test image path found.")
            return
            
        original_filename = os.path.basename(self.test_image_path)
        output_filename = os.path.splitext(original_filename)[0] + ".png"
        source_file = os.path.join(self.current_test_output_dir, output_filename)
        
        if not os.path.exists(source_file):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export Error", "Render result image not found.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Rendered Image", f"{output_filename}", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Rendered image exported successfully.")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export image: {str(e)}")




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
    
    def __init__(self, installed_families, local_versions, metadata_url):
        super().__init__()
        self.installed_families = installed_families
        self.local_versions = local_versions
        self.metadata_url = metadata_url

    def run(self):
        import urllib.request
        try:
            req = urllib.request.Request(self.metadata_url, headers={'User-Agent': 'Mozilla/5.0'})
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
    
    def __init__(self, updates_to_download, fonts_dir, css_url):
        super().__init__()
        self.updates_to_download = updates_to_download
        self.fonts_dir = fonts_dir
        self.css_url = css_url

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
                url = f"{self.css_url}{urllib.parse.quote(family)}:regular,italic,700,700italic"
                req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.81.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    css_content = response.read().decode('utf-8')
                
                blocks = re.findall(r'@font-face\s*\{([^}]+)\}', css_content)
                if not blocks:
                    url_fallback = f"{self.css_url}{urllib.parse.quote(family)}"
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
