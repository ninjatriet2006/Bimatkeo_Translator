from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
import html

class ConsoleWidget(QWidget):
    """Standalone UI component for the Live Log."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout.addStretch()
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_button)
        
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setFont(QFont("Consolas", 10))
        
        layout.addWidget(header_frame)
        layout.addWidget(self.log_textbox, stretch=1)
        
    @Slot(str, str)
    def insert_log(self, color: str, message: str):
        """Safely appends log text from any thread."""
        safe_message = html.escape(message)
        if not color or color.lower() in ["white", "default", "none"]:
            self.log_textbox.append(f'<span>{safe_message}</span>')
        else:
            self.log_textbox.append(f'<span style="color:{color};">{safe_message}</span>')
            
    @Slot()
    def clear_log(self):
        """Clears all text from the log box."""
        self.log_textbox.clear()
