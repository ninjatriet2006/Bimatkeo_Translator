"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.config_sync
- RESPONSIBILITY: Proxy online configuration synchronization.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.config_sync.manager.ConfigSyncManager
- IN = OUT: Instantiates ConfigSyncManager lazily and triggers config updates.
=============================================================================
"""

class ConfigSyncHandlersMixin:
    @property
    def config_sync_manager(self):
        if not hasattr(self, '_config_sync_manager_obj'):
            from app.core.desktop.logic.config_sync.manager import ConfigSyncManager
            cfg_loader = getattr(self, 'config_loader', None)
            base_dir = getattr(self, 'project_base_dir', '.')
            self._config_sync_manager_obj = ConfigSyncManager(cfg_loader, base_dir)
        return self._config_sync_manager_obj

    def _trigger_online_config_update_from_combo(self, key: str, combo):
        pass

    def _trigger_online_config_update(self, key: str):
        return self.config_sync_manager.trigger_online_config_update(key, main_window=self)

    def _trigger_all_configs_update(self):
        return self.config_sync_manager.trigger_all_configs_update(main_window=self)

    def _handle_config_update_finished(self, success, message):
        return self.config_sync_manager.handle_config_update_finished(success, message, main_window=self)

    def _reload_dynamic_configurations(self):
        return self.config_sync_manager.reload_dynamic_configurations(main_window=self)
