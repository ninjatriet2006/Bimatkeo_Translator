import os
from PySide6.QtWidgets import QInputDialog, QMessageBox, QComboBox
from PySide6.QtCore import QObject

class ApiProfileManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def get_api_profiles_file_path(self) -> str:
        base_dir = os.path.join(self.main_window.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'api_profiles.yaml')

    def load_api_profiles(self) -> dict:
        path = self.get_api_profiles_file_path()
        if os.path.exists(path):
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.load(f) or {}
                
                # Automigrate pool_profiles.yaml
                pool_path = self.main_window._get_yaml_config_path('pool_profiles.yaml')
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
                            self.main_window._save_yaml_config('api_profiles.yaml', data)
                        os.rename(pool_path, pool_path + ".migrated")
                    except Exception as e:
                        print(f"[ERROR] Pool Migration failed: {e}")
                return data
            except Exception as e:
                print(f"[ERROR] Failed to load API profiles: {e}")
        
        from dotenv import load_dotenv
        load_dotenv(os.path.join(self.main_window.project_base_dir, ".env"))

        return {
            "My Custom API": {
                "group": "Standalone",
                "endpoint": "",
                "model": "Auto",
                "key": ""
            }
        }

    def save_api_profiles(self, profiles: dict):
        self.main_window._save_yaml_config('api_profiles.yaml', profiles)

    def get_profile_mapping(self, service: str) -> dict:
        mappings = {
            "OCR": {'name': 'ocr_api_name', 'provider': 'api_ocr', 'endpoint': 'ocr_api_endpoint', 'model': 'ocr_api_model', 'key': 'ocr_api_key'},
            "Translator": {'name': 'api_name', 'provider': 'ai_translator', 'endpoint': 'ai_endpoint', 'model': 'ai_model', 'key': 'ai_key', 'max_retries': 'max_retries'},
        }
        return mappings.get(service, mappings["Translator"])

    def save_api_profile_generic(self, service: str):
        mapping = self.get_profile_mapping(service)
        name_widget = self.main_window.setting_widgets.get(mapping['name'])
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
            
        profile_name, ok = QInputDialog.getText(self.main_window, f"New {service} Profile", "Enter a name for the new API Profile:")
        if not ok:
            return
            
        profile_name = profile_name.strip()
        if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
            if hasattr(self.main_window, 'app_logger'):
                self.main_window.app_logger.log("WARNING", "Please enter a valid API Profile Name before saving.")
            return

        endpoint = self.main_window._get_value_from_widget(mapping['endpoint'], self.main_window.setting_widgets.get(mapping['endpoint'])) or ''
        provider = self.main_window._get_value_from_widget(mapping['provider'], self.main_window.setting_widgets.get(mapping['provider'])) or ''
        model = self.main_window._get_value_from_widget(mapping['model'], self.main_window.setting_widgets.get(mapping['model'])) or ''
        key = self.main_window._get_value_from_widget(mapping['key'], self.main_window.setting_widgets.get(mapping['key'])) or ''

        profiles = self.load_api_profiles()
        profiles[profile_name] = {
            "type": "Standalone",
            "service": service,
            "provider": provider,
            "endpoint": endpoint,
            "model": model,
            "key": key
        }
        self.save_api_profiles(profiles)

        filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("--- Select ---")
        combo.addItems(filtered_profiles)
        combo.setCurrentText(profile_name)
        combo.blockSignals(False)
        self.main_window.current_settings[mapping['name']] = profile_name

        if hasattr(self.main_window, 'app_logger'):
            self.main_window.app_logger.log("SUCCESS", f"API Profile '{profile_name}' saved to local config.")

    def delete_api_profile_generic(self, service: str):
        mapping = self.get_profile_mapping(service)
        name_widget = self.main_window.setting_widgets.get(mapping['name'])
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name or profile_name == "--- Select ---":
            return

        reply = QMessageBox.question(
            self.main_window,
            "Xác nhận xóa hồ sơ",
            f"Bạn có chắc chắn muốn xóa hồ sơ '{profile_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self.load_api_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            self.save_api_profiles(profiles)
            
            if hasattr(self.main_window, 'app_logger'):
                self.main_window.app_logger.log("SUCCESS", f"Đã xóa hồ sơ '{profile_name}'.")

            filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]

            combo.blockSignals(True)
            combo.clear()
            combo.addItem("--- Select ---")
            combo.addItems(filtered_profiles)
            combo.setCurrentText("--- Select ---")
            combo.blockSignals(False)
            self.on_api_profile_changed_generic("--- Select ---", service)
        else:
            if hasattr(self.main_window, 'app_logger'):
                self.main_window.app_logger.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")

    def clear_api_widgets_generic(self, service: str):
        mapping = self.get_profile_mapping(service)
        for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
            widget = self.main_window.setting_widgets.get(key)
            if widget:
                self.main_window.current_settings[key] = ""
                self.main_window._set_widget_value(key, "", widget)

    def on_api_profile_changed_generic(self, profile_name: str, service: str):
        profile_name = (profile_name or "").strip()
        mapping = self.get_profile_mapping(service)
        
        if not profile_name or profile_name.lower() in ["none", "--- select ---"]:
            self.main_window.current_settings[mapping['name']] = ""
            self.clear_api_widgets_generic(service)
            update_method = getattr(self.main_window, f"_update_{service.lower()}_visibility", None)
            if update_method: update_method()
            return
            
        profiles = self.load_api_profiles()
        if profile_name in profiles:
            profile = profiles[profile_name]
            
            self.main_window._loading_api_profile = True
            try:
                for field, key in [('provider', mapping['provider']), ('endpoint', mapping['endpoint']), ('model', mapping['model']), ('key', mapping['key'])]:
                    widget = self.main_window.setting_widgets.get(key)
                    if widget:
                        val = profile.get(field, '')
                        self.main_window.current_settings[key] = val
                        self.main_window._set_widget_value(key, val, widget)
            finally:
                self.main_window._loading_api_profile = False
        else:
            self.main_window.current_settings[mapping['name']] = profile_name
            self.clear_api_widgets_generic(service)
            
        update_method = getattr(self.main_window, f"_update_{service.lower()}_visibility", None)
        if update_method: update_method()
