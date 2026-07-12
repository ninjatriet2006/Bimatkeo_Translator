"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.console_widget
- RESPONSIBILITY: console_widget.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.console_widget.
=============================================================================
"""
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
        
        # Determine initial text based on parent if available
        initial_text = "Clear Log"
        if self.parent() and hasattr(self.parent(), "get_string"):
            initial_text = self.parent().get_string("ui_clear_log")
            if initial_text == "ui_clear_log":
                initial_text = "Clear Log"
                
        clear_button = QPushButton(initial_text)
        clear_button.setProperty("lang_id", "ui_clear_log")
        clear_button.setProperty("lang_type", "ui")
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
