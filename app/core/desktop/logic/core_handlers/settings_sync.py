"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.settings_sync
- RESPONSIBILITY: Proxy setting synchronization and widget value tracking.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.settings.sync.SettingsSyncManager, PySide6.QtWidgets
- IN = OUT: Instantiates SettingsSyncManager lazily and forwards config get/set.
=============================================================================
"""
from PySide6.QtWidgets import QWidget

class SettingsSyncHandlersMixin:
    @property
    def settings_sync_manager(self):
        if not hasattr(self, '_settings_sync_manager_obj'):
            from app.core.desktop.logic.settings.sync import SettingsSyncManager
            self._settings_sync_manager_obj = SettingsSyncManager(self)
        return self._settings_sync_manager_obj

    def _connect_widget_signal(self, key: str, widget: QWidget, context_key: str = None):
        return self.settings_sync_manager.connect_widget_signal(key, widget, context_key)

    def _on_setting_changed(self, key: str, context_key: str = None):
        return self.settings_sync_manager.on_setting_changed(key, context_key)

    def _get_value_from_widget(self, key: str, widget: QWidget) -> any:
        return self.settings_sync_manager.get_value_from_widget(key, widget)

    def _set_widget_value(self, key: str, value: any, widget: QWidget):
        return self.settings_sync_manager.set_widget_value(key, value, widget)

    def _load_app_state(self):
        return self.settings_sync_manager.load_app_state()

    def _save_app_state(self):
        return self.settings_sync_manager.save_app_state()

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
