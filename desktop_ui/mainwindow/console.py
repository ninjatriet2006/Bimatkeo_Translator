# type: ignore
# ===============================================================
# ConsoleMixin - Logging & Console Console Setup
#
# Author: User & Gemini Collaboration
# ===============================================================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ConsoleMixin:
    def _create_log_tab(self) -> QWidget:
        """Creates the content for the 'Live Log' tab."""
        container = QWidget()
        layout = QVBoxLayout(container)

        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.addStretch()  # Push button to the right
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self._clear_log)
        header_layout.addWidget(clear_button)

        # The main text widget for logging, set to read-only
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setFont(QFont("Consolas", 10))  # Use a monospaced font

        layout.addWidget(header_frame)
        layout.addWidget(self.log_textbox, stretch=1)
        return container

    def log(self, level: str, message: str):
        """
        Thread-safe method to log messages, with intelligent parsing for RAW backend output.
        It emits a signal that the main UI thread will catch.
        """
        # Fetch log colors dynamically to avoid circular import issues
        log_colors = getattr(self.config_loader, "log_colors", {})
        
        if level.upper() == "RAW":
            # For RAW messages from the backend, we don'\''t add our own prefix.
            # We pass the message through directly.
            raw_message = message.strip()
            msg_lower = raw_message.lower()

            # We can still re-classify the message type based on content for coloring.
            log_level_for_color = "INFO"  # Default for raw messages
            if msg_lower.startswith(('error:', 'validationerror:', 'exception:', 'traceback')):
                log_level_for_color = "ERROR"
            elif "out of memory" in msg_lower or "allocation failed" in msg_lower:
                log_level_for_color = "ERROR"

            color = log_colors.get(log_level_for_color, "default")
            # We emit the RAW message without any extra prefixes.
            self.log_signal.emit(color, raw_message)
        else:
            # For our own UI-generated logs (PIPELINE, SUCCESS, etc.), we add a prefix.
            color = log_colors.get(level.upper(), "default")
            msg_str = message.strip()
            self.log_signal.emit(color, f"[{level.upper()}] {msg_str}")
            
            # If the log contains progress like [1/10], parse and emit progress signal
            import re
            match = re.search(r"\[(\d+)/(\d+)\](.*)", msg_str)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                text = f"Processing {current}/{total} : {match.group(3).strip()}"
                self.pipeline_progress_signal.emit(current, total, text)


    def _insert_log_text(self, color: str, message: str):
        """
        This is the slot that receives the log signal. It safely updates the
        QTextEdit widget from the main UI thread.
        """
        import html
        safe_message = html.escape(message)
        # Use simple HTML to color the text
        if not color or color.lower() in ["white", "default", "none"]:
            self.log_textbox.append(f'<span>{safe_message}</span>')
        else:
            self.log_textbox.append(f'<span style="color:{color};">{safe_message}</span>')

    def _clear_log(self):
        """Clears all text from the log box."""
        self.log_textbox.clear()
