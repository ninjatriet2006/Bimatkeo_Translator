"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.custom_widgets.searchable_combo.popup
- RESPONSIBILITY: Provide the popup list for the searchable combo box.
- CALLED BY: app.core.desktop.components.custom_widgets.searchable_combo.combo_box
- CALLS TO: PySide6.QtWidgets
- IN = OUT: Instantiates a custom Qt popup widget.
=============================================================================
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QListWidget, QListWidgetItem,
    QApplication, QLineEdit
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QPalette, QCursor

class SearchableComboPopup(QWidget):
    def __init__(self, combo, parent=None):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("SearchableComboPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.combo = combo
        
        self.main_win = None
        app = QApplication.instance()
        if isinstance(app, QApplication):
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    self.main_win = widget
                    break
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)
        
        self.list_widget = QListWidget(self)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        self.installEventFilter(self)
        self.search_edit.installEventFilter(self)
        self.list_widget.installEventFilter(self)
        
        self._apply_popup_theme()

    def _apply_popup_theme(self):
        app = QApplication.instance()
        main_win = None
        if isinstance(app, QApplication):
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    main_win = widget
                    break
        
        if main_win and getattr(main_win, 'theme_colors', None):
            colors = main_win.theme_colors
            bg = colors.get("background_frame", "#2c2c2c")
            bg_input = colors.get("background_main", "#1e1e1e")
            txt = colors.get("text_main", "#dce4ee")
            border = colors.get("border", "#555555")
            accent = colors.get("accent", "#3a7ebf")
            hover = colors.get("primary_button_hover", "#444444")
        else:
            palette = QApplication.palette()
            bg = palette.color(QPalette.ColorRole.Window).name()
            bg_input = palette.color(QPalette.ColorRole.Base).name()
            txt = palette.color(QPalette.ColorRole.WindowText).name()
            border = palette.color(QPalette.ColorRole.Mid).name()
            accent = palette.color(QPalette.ColorRole.Highlight).name()
            hover = palette.color(QPalette.ColorRole.Button).lighter(105).name()
            
        self.setStyleSheet(f"""
            #SearchableComboPopup {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {bg_input};
                color: {txt};
                border: 1px solid {border};
                padding: 4px;
                border-radius: 3px;
            }}
            QListWidget {{
                background-color: {bg};
                color: {txt};
                border: none;
            }}
            QListWidget::item {{
                padding: 5px;
                border-radius: 2px;
                background-color: transparent;
                border: none;
            }}
            QListWidget::item:hover {{
                background-color: {hover};
                color: {txt};
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

    def populate(self):
        self._apply_popup_theme()
        self.list_widget.clear()
        self.items_data = []
        for i in range(self.combo.count()):
            text = self.combo.itemText(i)
            item_model = self.combo.model().index(i, 0)
            is_enabled = bool(self.combo.model().flags(item_model) & Qt.ItemFlag.ItemIsEnabled)
            user_data = self.combo.itemData(i)
            self.items_data.append((text, is_enabled, i, user_data))
            
        self.search_edit.blockSignals(True)
        self.search_edit.setText("")
        self.search_edit.blockSignals(False)
        self._filter_items()
        self.search_edit.setFocus()

    def _filter_items(self):
        search_text = self.search_edit.text().lower()
        self.list_widget.clear()
        
        self.current_visible_mappings = []
        selected_row = -1
        
        is_font_combo = self.combo.findText("🔍 Install New Font...") != -1
        
        for text, is_enabled, orig_index, user_data in self.items_data:
            if search_text in text.lower():
                item = QListWidgetItem(text)
                if not is_enabled:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    item.setForeground(QColor("#888888"))
                elif is_font_combo and text not in ["🔍 Install New Font...", "📥 Update All Fonts..."]:
                    if self.main_win and hasattr(self.main_win, "_get_google_font_family_from_filename"):
                        actual_font = user_data if user_data else text
                        is_google = self.main_win._get_google_font_family_from_filename(actual_font) is not None
                        if not is_google:
                            item.setForeground(QColor("#888888"))
                            item.setToolTip("Custom font (manual copy, not from Google Fonts)")
                elif "(Not Setup)" in text or "(Incomplete)" in text:
                    item.setForeground(QColor("#a8a8a8"))
                    item.setToolTip("Model weights not found. Check model configs.")
                self.list_widget.addItem(item)
                self.current_visible_mappings.append(orig_index)
                
                if orig_index == self.combo.currentIndex():
                    selected_row = self.list_widget.count() - 1
                    self.list_widget.setCurrentItem(item)

        if selected_row != -1:
            self.list_widget.setCurrentRow(selected_row)
            
        self.adjust_size()

    def adjust_size(self):
        row_height = 28
        item_count = min(7, self.list_widget.count())
        if item_count == 0:
            item_count = 1
        
        list_height = item_count * row_height + 4
        total_height = 26 + 16 + list_height
        
        self.setFixedWidth(max(self.combo.width(), 200))
        self.setFixedHeight(total_height)

    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        if 0 <= row < len(self.current_visible_mappings):
            orig_index = self.current_visible_mappings[row]
            self.combo.setCurrentIndex(orig_index)
            if self.combo.isEditable() and self.combo.lineEdit():
                self.combo.lineEdit().setText(self.combo.itemText(orig_index))
        self.close()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item and (current_item.flags() & Qt.ItemFlag.ItemIsEnabled):
                    self._on_item_clicked(current_item)
                else:
                    self.close()
                return True
            elif event.key() == Qt.Key.Key_Down:
                if obj == self.search_edit:
                    self.list_widget.setFocus()
                    if self.list_widget.count() > 0 and self.list_widget.currentRow() == -1:
                        self.list_widget.setCurrentRow(0)
                    return True
                elif obj == self.list_widget:
                    curr_row = self.list_widget.currentRow()
                    if curr_row < self.list_widget.count() - 1:
                        self.list_widget.setCurrentRow(curr_row + 1)
                    return True
            elif event.key() == Qt.Key.Key_Up:
                if obj == self.list_widget:
                    curr_row = self.list_widget.currentRow()
                    if curr_row > 0:
                        self.list_widget.setCurrentRow(curr_row - 1)
                    else:
                        self.search_edit.setFocus()
                    return True
        elif event.type() == QEvent.Type.MouseButtonPress:
            if not self.geometry().contains(QCursor.pos()):
                self.close()
                return True
        return super().eventFilter(obj, event)
