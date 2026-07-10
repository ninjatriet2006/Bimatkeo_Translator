"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.pool_dialog.dialog
- RESPONSIBILITY: Main wrapper class for ManagePoolsDialog.
- CALLED BY: app.core.desktop.components.settings_panel, app.core.desktop.logic.core_handlers
- CALLS TO: ui_builder, pool_actions, api_actions, fetch_actions
- IN = OUT: Integrates separated actions into a single PySide6 Dialog.
=============================================================================
"""
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Signal

from app.core.desktop.components.pool_dialog.ui_builder import build_ui
from app.core.desktop.components.pool_dialog.actions import pool_actions
from app.core.desktop.components.pool_dialog.actions import api_actions
from app.core.desktop.components.pool_dialog.actions import fetch_actions

class ManagePoolsDialog(QDialog):
    models_fetched_signal = Signal(list)
    fetch_finished_signal = Signal()

    def __init__(self, main_window, service="Translator"):
        super().__init__(main_window)
        self.main_window = main_window
        self.service = service
        self.setWindowTitle("Manage API Pools")
        self.resize(500, 600)
        
        # Load data
        self.pools = self.main_window._load_pool_profiles(self.service)
        self.api_profiles = self.main_window._load_api_profiles()
        
        # Build UI
        build_ui(self)
        
        # Initial states
        pool_actions.refresh_pool_selector(self)
        
        # Signals
        self.models_fetched_signal.connect(self._show_fetched_models)
        self.fetch_finished_signal.connect(self._on_fetch_finished)

    # --- Pool Actions ---
    def _refresh_pool_selector(self):
        pool_actions.refresh_pool_selector(self)

    def _on_pool_changed(self, pool_name):
        pool_actions.on_pool_changed(self, pool_name)

    def _save_pool(self):
        pool_actions.save_pool(self)

    def _create_new_pool(self):
        pool_actions.create_new_pool(self)

    def _delete_pool(self):
        pool_actions.delete_pool(self)

    # --- API Actions ---
    def _move_item(self, offset):
        api_actions.move_item(self, offset)

    def _remove_from_pool(self):
        api_actions.remove_from_pool(self)

    def _add_existing_to_pool(self):
        api_actions.add_existing_to_pool(self)

    def _add_new_to_pool(self):
        api_actions.add_new_to_pool(self)

    # --- Fetch Actions ---
    def _fetch_models(self):
        fetch_actions.fetch_models(self)

    def _show_fetched_models(self, models):
        fetch_actions.show_fetched_models(self, models)

    def _on_fetch_finished(self):
        fetch_actions.on_fetch_finished(self)
