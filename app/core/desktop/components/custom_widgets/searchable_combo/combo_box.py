"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.custom_widgets.searchable_combo.combo_box
- RESPONSIBILITY: Provide a combo box with search functionality.
- CALLED BY: UI classes in app.core.desktop
- CALLS TO: PySide6.QtWidgets, app.core.desktop.components.custom_widgets.searchable_combo.popup
- IN = OUT: Instantiates a custom Qt widget.
=============================================================================
"""
from PySide6.QtWidgets import QComboBox, QApplication
from PySide6.QtCore import QPoint
from app.core.desktop.components.custom_widgets.searchable_combo.popup import SearchableComboPopup

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup_widget = None

    def showPopup(self):
        if not self.popup_widget:
            self.popup_widget = SearchableComboPopup(self)
        
        self.popup_widget.populate()
        
        pos = self.mapToGlobal(QPoint(0, self.height()))
        
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            popup_height = self.popup_widget.height()
            if pos.y() + popup_height > screen_geom.bottom():
                pos = self.mapToGlobal(QPoint(0, -popup_height))
                
        self.popup_widget.move(pos)
        self.popup_widget.show()

    def hidePopup(self):
        if self.popup_widget:
            self.popup_widget.close()
        super().hidePopup()
