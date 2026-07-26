"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.api_profile.manager
- RESPONSIBILITY: Decoupled logic manager for API Profiles (save, load, delete) and profile mappings.
- CALLED BY: app.core.desktop.logic.core_handlers.api_profile, app.core.desktop.main_window
- CALLS TO: app.core.api.profile.profile_storage.*, app.core.desktop.logic.api_profile.actions
- IN = OUT: Primitive parameter project_base_dir into __init__, PySide6 Signals for notifications.
=============================================================================
"""
from PySide6.QtCore import QObject, Signal

from app.core.api.profile.profile_storage import load_api_profiles, save_api_profiles, get_api_profiles_file_path

from app.core.desktop.logic.api_profile.actions import save_api_profile_generic
from app.core.desktop.logic.api_profile.actions import delete_api_profile_generic
from app.core.desktop.logic.api_profile.actions import clear_api_widgets_generic
from app.core.desktop.logic.api_profile.actions import on_api_profile_changed_generic

class ApiProfileManager(QObject):
    profile_changed = Signal(str, dict)  # (service, profile_data)
    profile_saved = Signal(str, str)     # (service, profile_name)
    profile_deleted = Signal(str, str)   # (service, profile_name)

    def __init__(self, project_base_dir: str = "."):
        super().__init__()
        self.project_base_dir = project_base_dir

    def get_api_profiles_file_path(self) -> str:
        return get_api_profiles_file_path(self.project_base_dir)

    def load_api_profiles(self, context=None) -> dict:
        ctx = context if context is not None else self.project_base_dir
        return load_api_profiles(ctx)

    def save_api_profiles(self, profiles: dict, context=None):
        ctx = context if context is not None else self.project_base_dir
        save_api_profiles(ctx, profiles)

    def get_profile_mapping(self, service: str) -> dict:
        from .mapping import get_profile_mapping as _get_mapping
        return _get_mapping(service)

    def save_api_profile_generic(self, main_window, service: str):
        save_api_profile_generic(main_window, service)

    def delete_api_profile_generic(self, main_window, service: str):
        delete_api_profile_generic(main_window, service)

    def clear_api_widgets_generic(self, main_window, service: str):
        clear_api_widgets_generic(main_window, service)

    def on_api_profile_changed_generic(self, main_window, profile_name: str, service: str):
        on_api_profile_changed_generic(main_window, profile_name, service)

