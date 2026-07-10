"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.api_profile
- RESPONSIBILITY: Proxy API Profile operations for the UI layer.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.api_profile.manager.ApiProfileManager
- IN = OUT: Instantiates ApiProfileManager lazily and forwards requests.
=============================================================================
"""

class ApiProfileHandlersMixin:
    @property
    def _api_profile_mgr(self):
        if not hasattr(self, '__api_profile_mgr'):
            from app.core.desktop.logic.api_profile.manager import ApiProfileManager
            self.__api_profile_mgr = ApiProfileManager(self)
        return self.__api_profile_mgr

    def _get_api_profiles_file_path(self) -> str:
        return self._api_profile_mgr.get_api_profiles_file_path()

    def _load_api_profiles(self) -> dict:
        return self._api_profile_mgr.load_api_profiles()

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
        from app.core.desktop.components.pool_dialog.dialog import ManagePoolsDialog
        dialog = ManagePoolsDialog(self, service)
        dialog.exec()
