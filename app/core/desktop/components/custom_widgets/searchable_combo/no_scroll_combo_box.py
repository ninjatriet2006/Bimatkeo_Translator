"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.custom_widgets.searchable_combo.no_scroll_combo_box
- RESPONSIBILITY: Provide a combo box that ignores wheel events to prevent accidental scrolling.
- CALLED BY: UI classes in app.core.desktop
- CALLS TO: app.core.desktop.components.custom_widgets.searchable_combo.combo_box.SearchableComboBox
- IN = OUT: Instantiates a custom Qt widget.
=============================================================================
"""
from PySide6.QtCore import QEvent
from app.core.desktop.components.custom_widgets.searchable_combo.combo_box import SearchableComboBox

class NoScrollComboBox(SearchableComboBox):
    """A custom QComboBox that ignores wheel events to prevent accidental scrolling."""
    def wheelEvent(self, event: QEvent):
        event.ignore()
