"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.preview_widgets.file_explorer_panel
- RESPONSIBILITY: Provide a QListWidget to list images in a directory.
- CALLED BY: app.core.desktop.logic.pipeline_runner.preview_tester
- CALLS TO: None
- IN = OUT: Emits file_selected signal.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon
import os

class FileExplorerPanel(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
        
        self.current_folder = ""
        
        self.layout_obj = QVBoxLayout(self)
        self.layout_obj.setContentsMargins(5, 5, 5, 5)
        
        # Header
        self.lbl_header = QLabel("File List", self)
        self.lbl_header.setStyleSheet("font-weight: bold;")
        self.layout_obj.addWidget(self.lbl_header)
        
        # Select Folder Button
        self.btn_select_folder = QPushButton("Select Folder", self)
        self.btn_select_folder.clicked.connect(self._on_select_folder)
        self.layout_obj.addWidget(self.btn_select_folder)
        
        # List Widget
        self.list_widget = QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self._on_item_selected)
        self.layout_obj.addWidget(self.list_widget)

    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder", self.current_folder)
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder_path: str):
        self.current_folder = folder_path
        self.list_widget.clear()
        
        if not os.path.exists(folder_path):
            return
            
        valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        files = []
        for f in os.listdir(folder_path):
            if os.path.splitext(f.lower())[1] in valid_exts:
                files.append(f)
                
        files.sort()
        for f in files:
            item = QListWidgetItem(f)
            item.setData(Qt.ItemDataRole.UserRole, os.path.join(folder_path, f))
            self.list_widget.addItem(item)

    def _on_item_selected(self):
        items = self.list_widget.selectedItems()
        if items:
            file_path = items[0].data(Qt.ItemDataRole.UserRole)
            self.file_selected.emit(file_path)

    def select_file(self, file_path: str):
        # Automatically select the file in the list if it exists
        if not file_path:
            return
        
        folder = os.path.dirname(file_path)
        if folder != self.current_folder:
            self.load_folder(folder)
            
        # Block signals to avoid re-triggering file_selected
        self.list_widget.blockSignals(True)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.list_widget.setCurrentItem(item)
                break
        self.list_widget.blockSignals(False)
