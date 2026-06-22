# type: ignore
# ===============================================================
# Widgets Helper and Utility Classes
#
# Author: User & Gemini Collaboration
# ===============================================================

import os
import sys
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QListWidget, QListWidgetItem,
    QApplication, QComboBox, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QEvent, QPoint
from PySide6.QtGui import QColor, QPalette, QCursor

# Helper to read credentials from environment / keys.yaml
def get_provider_credentials(provider: str) -> dict:
    # Try to load from keys.yaml first
    keys_vars = {}
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    keys_path = os.path.join(base_dir, ".config", "configs", "keys.yaml")
    if os.path.exists(keys_path):
        try:
            with open(keys_path, 'r', encoding='utf-8') as f:
                content = yaml.load(f)
            if isinstance(content, dict):
                for k, v in content.items():
                    if k:
                        keys_vars[str(k)] = str(v) if v is not None else ""
        except Exception:
            pass

    def get_val(env_name, default=""):
        return keys_vars.get(env_name) or os.getenv(env_name, default)

    if provider == 'gemini':
        return {
            "endpoint": get_val("GEMINI_API_ENDPOINT", "https://generativelanguage.googleapis.com"),
            "model": get_val("GEMINI_API_MODEL", "Auto"),
            "key": get_val("GEMINI_API_KEY", "")
        }
    elif provider == 'openai':
        return {
            "endpoint": get_val("OPENAI_API_ENDPOINT", "https://api.openai.com/v1"),
            "model": get_val("OPENAI_API_MODEL", "Auto"),
            "key": get_val("OPENAI_API_KEY", "")
        }
    return {
        "endpoint": get_val(f"{provider.upper()}_API_ENDPOINT", ""),
        "model": get_val(f"{provider.upper()}_API_MODEL", "Auto"),
        "key": get_val(f"{provider.upper()}_API_KEY", "")
    }


class DynamicHeightListWidget(QListWidget):
    """
    A custom QListWidget that:
    1. Overrides its size hints to always match its content's height.
    2. Disables its own vertical scrollbar, forcing the parent to scroll.
    3. Ignores mouse wheel events to prevent accidental scrolling inside parent.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def minimumSizeHint(self) -> QSize:
        """Override to report the content's height as the minimum possible height."""
        height = self._get_content_height()
        return QSize(super().minimumSizeHint().width(), height)

    def sizeHint(self) -> QSize:
        """Override to report the content's height as the preferred height."""
        height = self._get_content_height()
        return QSize(super().sizeHint().width(), height)

    def wheelEvent(self, event: QEvent):
        """Pass the wheel event to the parent to allow scrolling the main area."""
        event.ignore()

    def _get_content_height(self) -> int:
        """Calculates the total height required to display all items without scrolling."""
        if self.count() == 0:
            return 35  # Return a default small height when empty

        # Sum of the height of each item in the list
        content_height = 0
        for i in range(self.count()):
            content_height += self.sizeHintForRow(i)

        # Add the height of the frame around the content
        content_height += self.frameWidth() * 2

        return content_height


class SearchableComboPopup(QWidget):
    def __init__(self, combo, parent=None):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("SearchableComboPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.combo = combo
        
        # Store main window reference
        self.main_win = None
        for widget in QApplication.instance().topLevelWidgets():
            if isinstance(widget, QMainWindow):
                self.main_win = widget
                break
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Search Line Edit
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)
        
        # List Widget
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
            # Fallback to system palette for Default Qt (which should be light/system matching)
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
                        # user_data is available in self.items_data
                        actual_font = user_data if user_data else text
                        is_google = self.main_win._get_google_font_family_from_filename(actual_font) is not None
                        if not is_google:
                            item.setForeground(QColor("#888888"))
                            item.setToolTip("Custom font (manual copy, not from Google Fonts)")
                elif "(Not Setup)" in text:
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


class SearchableFontInstallDialog(QDialog):
    def __init__(self, google_fonts, default_font=None, parent=None):
        super().__init__(parent)
        self.google_fonts = google_fonts
        self.selected_font = None
        self.init_ui(default_font)

    def init_ui(self, default_font):
        self.setWindowTitle("Cài đặt Phông chữ từ Google Fonts")
        self.resize(380, 480)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Label instruction
        lbl = QLabel("Tìm kiếm hoặc nhập trực tiếp tên phông chữ từ Google Fonts để cài đặt:", self)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        # Search line edit
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Nhập tên phông chữ (Ví dụ: Bangers, Roboto...)")
        self.search_edit.textChanged.connect(self.filter_fonts)
        layout.addWidget(self.search_edit)

        # List widget for popular fonts
        self.list_widget = QListWidget(self)
        for font in self.google_fonts:
            item = QListWidgetItem(font)
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_install = QPushButton("Cài đặt", self)
        self.btn_install.setDefault(True)
        self.btn_install.clicked.connect(self.on_install_clicked)
        btn_layout.addWidget(self.btn_install)

        self.btn_cancel = QPushButton("Hủy bỏ", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        # If a default font is specified, pre-select it and put its text in the search edit
        if default_font:
            # Clean default font name from suffix
            clean_default = default_font
            for suffix in ["-Regular", "-Bold", "-Italic", "-BoldItalic"]:
                if default_font.endswith(suffix):
                    clean_default = default_font[:-len(suffix)]
                    break
            # Or clean from extension
            if clean_default.lower().endswith(".ttf"):
                clean_default = clean_default[:-4]
            # Replace family spacing if it matches one of ours
            for gf in self.google_fonts:
                if gf.replace(" ", "").lower() == clean_default.replace(" ", "").lower():
                    clean_default = gf
                    break
            
            self.search_edit.setText(clean_default)
            # Find and select the item in the list
            items = self.list_widget.findItems(clean_default, Qt.MatchFlag.MatchExactly)
            if items:
                self.list_widget.setCurrentItem(items[0])

    def filter_fonts(self, text):
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def on_item_double_clicked(self, item):
        self.selected_font = item.text()
        self.accept()

    def on_install_clicked(self):
        curr_item = self.list_widget.currentItem()
        search_text = self.search_edit.text().strip()
        
        # If there is a selected item in list widget and it is NOT hidden by filter
        if curr_item and not curr_item.isHidden():
            self.selected_font = curr_item.text()
        elif search_text:
            self.selected_font = search_text
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập hoặc chọn một phông chữ để cài đặt.")
            return
            
        self.accept()


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup_widget = None

    def showPopup(self):
        if not self.popup_widget:
            self.popup_widget = SearchableComboPopup(self)
        
        self.popup_widget.populate()
        
        # Position the popup
        pos = self.mapToGlobal(QPoint(0, self.height()))
        
        # Prevent going off screen
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            popup_height = self.popup_widget.height()
            if pos.y() + popup_height > screen_geom.bottom():
                # Show above
                pos = self.mapToGlobal(QPoint(0, -popup_height))
                
        self.popup_widget.move(pos)
        self.popup_widget.show()

    def hidePopup(self):
        if self.popup_widget:
            self.popup_widget.close()
        super().hidePopup()


class NoScrollComboBox(SearchableComboBox):
    """A custom QComboBox that ignores wheel events to prevent accidental scrolling."""

    def wheelEvent(self, event: QEvent):
        # Ignore the event completely, passing it to the parent widget (the scroll area)
        event.ignore()
