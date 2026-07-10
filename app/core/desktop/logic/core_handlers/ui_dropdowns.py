"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.ui_dropdowns
- RESPONSIBILITY: Proxy UI dropdown filtering and length label updates.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.ui_updates.dropdowns.UIDropdownManager
- IN = OUT: Instantiates UIDropdownManager lazily and forwards filtering logic.
=============================================================================
"""
from PySide6.QtWidgets import QComboBox

class UIDropdownsHandlersMixin:
    @property
    def ui_dropdown_manager(self):
        if not hasattr(self, '_ui_dropdown_manager_obj'):
            from app.core.desktop.logic.ui_updates.dropdowns import UIDropdownManager
            self._ui_dropdown_manager_obj = UIDropdownManager(self)
        return self._ui_dropdown_manager_obj

    def _update_max_length_label(self):
        return self.ui_dropdown_manager.update_max_length_label()

    def _on_translator_changed(self, translator_name: str):
        return self.ui_dropdown_manager.on_translator_changed(translator_name)

    def _is_translator_supported_for_target(self, translator_name: str, target_code: str) -> bool:
        return self.ui_dropdown_manager.is_translator_supported_for_target(translator_name, target_code)

    def _filter_translator_dropdowns(self, target_lang_name: str, context_key: str = None):
        return self.ui_dropdown_manager.filter_translator_dropdowns(target_lang_name, context_key)

    def _filter_chain_step_translator_dropdown(self, target_lang_name: str, translator_combo: QComboBox):
        return self.ui_dropdown_manager.filter_chain_step_translator_dropdown(target_lang_name, translator_combo)

    def _on_target_lang_changed(self, target_lang_name: str):
        return self.ui_dropdown_manager.on_target_lang_changed(target_lang_name)

    def _filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        return self.ui_dropdown_manager.filter_language_dropdown(translator_name, lang_combo)
