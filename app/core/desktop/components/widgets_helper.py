"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widgets_helper
- RESPONSIBILITY: widgets_helper.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.widgets_helper.
=============================================================================
"""
from app.core.desktop.components.custom_widgets.dynamic_height_list import DynamicHeightListWidget
from app.core.desktop.components.custom_widgets.searchable_combo.popup import SearchableComboPopup
from app.core.desktop.components.custom_widgets.searchable_combo.combo_box import SearchableComboBox
from app.core.desktop.components.custom_widgets.searchable_combo.no_scroll_combo_box import NoScrollComboBox
from app.core.desktop.components.custom_widgets.font_install_dialog import SearchableFontInstallDialog

__all__ = [
    'DynamicHeightListWidget',
    'SearchableComboPopup',
    'SearchableComboBox',
    'NoScrollComboBox',
    'SearchableFontInstallDialog'
]
