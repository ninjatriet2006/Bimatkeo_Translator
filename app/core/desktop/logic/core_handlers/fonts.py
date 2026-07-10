"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.fonts
- RESPONSIBILITY: Proxy font UI management operations.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.fonts.ui_manager.FontUIManager
- IN = OUT: Instantiates FontUIManager lazily and routes font-related commands.
=============================================================================
"""

class FontHandlersMixin:
    @property
    def font_ui_manager(self):
        if not hasattr(self, '_font_ui_manager_obj'):
            from app.core.desktop.logic.fonts.ui_manager import FontUIManager
            self._font_ui_manager_obj = FontUIManager(self)
        return self._font_ui_manager_obj

    def _get_fonts_manager(self):
        return self.font_ui_manager.get_fonts_manager()

    def _build_font_map(self):
        return self.font_ui_manager.build_font_map()

    def _get_google_font_family_from_filename(self, filename: str) -> str:
        return self.font_ui_manager.get_google_font_family_from_filename(filename)

    def _get_installed_google_fonts(self) -> dict:
        return self.font_ui_manager.get_installed_google_fonts()

    def _save_font_version_from_online_metadata(self, font_family: str):
        return self.font_ui_manager.save_font_version_from_online_metadata(font_family)

    def _force_update_current_font(self, main_font_combo):
        return self.font_ui_manager.force_update_current_font(main_font_combo)

    def _prompt_font_install(self, main_font_combo, pre_selected_font=None):
        return self.font_ui_manager.prompt_font_install(main_font_combo, pre_selected_font)

    def _find_similar_font(self, main_font_combo):
        return self.font_ui_manager.find_similar_font(main_font_combo)

    def _check_and_update_all_fonts(self, main_font_combo):
        return self.font_ui_manager.check_and_update_all_fonts(main_font_combo)

    def _download_updates(self, updates, main_font_combo):
        return self.font_ui_manager.download_updates(updates, main_font_combo)

    def _delete_font(self, font_name: str):
        return self.font_ui_manager.delete_font(font_name)
