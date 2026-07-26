"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.custom_widgets.font_install_dialog
- RESPONSIBILITY: Provide a dialog for searching and installing fonts.
- CALLED BY: app.core.desktop.logic.fonts.actions.install_action
- CALLS TO: PySide6.QtWidgets.QDialog
- IN = OUT: Instantiates a custom Qt dialog.
=============================================================================
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

class SearchableFontInstallDialog(QDialog):
    def __init__(self, google_fonts, default_font=None, parent=None):
        super().__init__(parent)
        self.google_fonts = google_fonts
        self.selected_font = None
        self.init_ui(default_font)

    def init_ui(self, default_font):
        self.setWindowTitle("Cài đặt Phông chữ từ Google Fonts")
        self.setProperty("lang_id", "ui_font_dialog_title")
        self.setProperty("lang_type", "ui")
        self.resize(380, 480)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        lbl = QLabel("Tìm kiếm hoặc nhập trực tiếp tên phông chữ từ Google Fonts để cài đặt:", self)
        lbl.setProperty("lang_id", "ui_font_dialog_instruction")
        lbl.setProperty("lang_type", "ui")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Nhập tên phông chữ (Ví dụ: Bangers, Roboto...)")
        self.search_edit.textChanged.connect(self.filter_fonts)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget(self)
        for font in self.google_fonts:
            item = QListWidgetItem(font)
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_install = QPushButton("Cài đặt", self)
        self.btn_install.setProperty("lang_id", "ui_btn_install")
        self.btn_install.setProperty("lang_type", "ui")
        self.btn_install.setDefault(True)
        self.btn_install.clicked.connect(self.on_install_clicked)
        btn_layout.addWidget(self.btn_install)

        self.btn_cancel = QPushButton("Hủy bỏ", self)
        self.btn_cancel.setProperty("lang_id", "ui_btn_cancel")
        self.btn_cancel.setProperty("lang_type", "ui")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        if default_font:
            clean_default = default_font
            for suffix in ["-Regular", "-Bold", "-Italic", "-BoldItalic"]:
                if default_font.endswith(suffix):
                    clean_default = default_font[:-len(suffix)]
                    break
            if clean_default.lower().endswith(".ttf"):
                clean_default = clean_default[:-4]
            for gf in self.google_fonts:
                if gf.replace(" ", "").lower() == clean_default.replace(" ", "").lower():
                    clean_default = gf
                    break
            
            self.search_edit.setText(clean_default)
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
        
        if curr_item and not curr_item.isHidden():
            self.selected_font = curr_item.text()
        elif search_text:
            self.selected_font = search_text
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập hoặc chọn một phông chữ để cài đặt.")
            return
            
        self.accept()
