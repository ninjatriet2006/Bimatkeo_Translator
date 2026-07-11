"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.themes
- RESPONSIBILITY: Proxy theme operations.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.theme_manager.ThemeManager
- IN = OUT: Instantiates ThemeManager lazily and forwards theme changes.
=============================================================================
"""
import os

class ThemeHandlersMixin:
    @property
    def theme_manager(self):
        if not hasattr(self, '_theme_manager_obj'):
            from app.core.desktop.logic.theme_manager import ThemeManager
            self._theme_manager_obj = ThemeManager(self)
        return self._theme_manager_obj

    def _load_themes(self):
        return self.theme_manager.load_themes()

    def _apply_theme(self, theme_name: str):
        return self.theme_manager.apply_theme(theme_name)

    def _on_font_scale_changed(self, text: str):
        current_theme_name = self.theme_combobox.currentText()
        self._apply_theme(current_theme_name)
