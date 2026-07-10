"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.tooltips
- RESPONSIBILITY: Update and show dynamic capabilities for UI fields.
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: app.core.shared_registry.TranslatorFactory
- IN = OUT: Computes string for tooltips and updates target widgets.
=============================================================================
"""

from typing import Any

class TooltipsBuilderMixin:
    mw: Any
    def update_translator_tooltip(self, translator_name: str):
        import app.core.desktop.main_window as mw_module
        category = self.mw._get_active_translator_category()
        key = 'offline_translator' if category == 'offline' else 'ai_translator'
        translator_combo = self.mw.setting_widgets.get(key)
        if not translator_combo:
            return

        from app.core.shared_registry import TranslatorFactory
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        code_to_name = {v: k for k, v in mw_module.LANGUAGES.items()}

        label = self.mw.config_loader.format_display_label(translator_name, key)
        header = label if label == translator_name else f"{label} ({translator_name})"
        tooltip_html = f"<b>{header} Capabilities:</b><hr>"

        if not capabilities:
            tooltip_html += "No translation is performed."
        elif capabilities.get('__any__') == '__all__':
            tooltip_html += "Supports translation between most languages."
        else:
            lines = []
            for source_code, target_codes in capabilities.items():
                source_name = code_to_name.get(source_code, source_code)
                target_names = [str(code_to_name.get(tc, tc)) for tc in target_codes]
                lines.append(f"<b>From {str(source_name)}:</b><br>  → {', '.join(target_names)}")
            tooltip_html += "<br>".join(lines)

        translator_combo.setToolTip(tooltip_html)
