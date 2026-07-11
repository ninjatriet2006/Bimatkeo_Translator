"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.api_profile.manager
- RESPONSIBILITY: Manage API Profiles logic (save, load, delete) and provide widget mappings.
- CALLED BY: app.core.desktop.logic.core_handlers.api_profile
- CALLS TO: app.core.api_profile.storage.*, app.core.desktop.logic.api_profile.actions
- IN = OUT: Routes generic profile operations to specific implementations.
=============================================================================
"""
from PySide6.QtCore import QObject

from app.core.api_profile.storage.paths import get_api_profiles_file_path
from app.core.api_profile.storage.reader import load_api_profiles
from app.core.api_profile.storage.writer import save_api_profiles

from app.core.desktop.logic.api_profile.actions import save_api_profile_generic
from app.core.desktop.logic.api_profile.actions import delete_api_profile_generic
from app.core.desktop.logic.api_profile.actions import clear_api_widgets_generic
from app.core.desktop.logic.api_profile.actions import on_api_profile_changed_generic

class ApiProfileManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def get_api_profiles_file_path(self) -> str:
        return get_api_profiles_file_path(self.main_window.project_base_dir)

    def load_api_profiles(self) -> dict:
        return load_api_profiles(self.main_window)

    def save_api_profiles(self, profiles: dict):
        save_api_profiles(self.main_window, profiles)

    def get_profile_mapping(self, service: str) -> dict:
        mappings = {
            "OCR": {'name': 'ocr_api_name', 'provider': 'api_ocr', 'endpoint': 'ocr_api_endpoint', 'model': 'ocr_api_model', 'key': 'ocr_api_key'},
            "Translator": {'name': 'api_name', 'provider': 'ai_translator', 'endpoint': 'ai_endpoint', 'model': 'ai_model', 'key': 'ai_key', 'max_retries': 'max_retries'},
        }
        return mappings.get(service, mappings["Translator"])

    def save_api_profile_generic(self, service: str):
        save_api_profile_generic(self.main_window, service)

    def delete_api_profile_generic(self, service: str):
        delete_api_profile_generic(self.main_window, service)

    def clear_api_widgets_generic(self, service: str):
        clear_api_widgets_generic(self.main_window, service)

    def on_api_profile_changed_generic(self, profile_name: str, service: str):
        on_api_profile_changed_generic(self.main_window, profile_name, service)
