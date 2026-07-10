import re
from PySide6.QtCore import QObject, Signal

class AppLogger(QObject):
    """Handles log parsing, coloring and progress extraction."""
    log_signal = Signal(str, str)
    pipeline_progress_signal = Signal(int, int, str)
    
    def __init__(self, config_loader=None, parent=None):
        super().__init__(parent)
        self.config_loader = config_loader
        
    def log(self, level: str, message: str):
        log_colors = getattr(self.config_loader, "log_colors", {}) if self.config_loader else {}
        
        if level.upper() == "RAW":
            raw_message = message.strip()
            msg_lower = raw_message.lower()
            
            log_level_for_color = "INFO"
            if msg_lower.startswith(('error:', 'validationerror:', 'exception:', 'traceback')):
                log_level_for_color = "ERROR"
            elif "out of memory" in msg_lower or "allocation failed" in msg_lower:
                log_level_for_color = "ERROR"
                
            color = log_colors.get(log_level_for_color, "default")
            self.log_signal.emit(color, raw_message)
        else:
            color = log_colors.get(level.upper(), "default")
            msg_str = message.strip()
            self.log_signal.emit(color, f"[{level.upper()}] {msg_str}")
            
            match = re.search(r"\[(\d+)/(\d+)\](.*)", msg_str)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                text = f"Processing {current}/{total} : {match.group(3).strip()}"
                self.pipeline_progress_signal.emit(current, total, text)
