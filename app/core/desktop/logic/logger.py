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
        
        lang_id = getattr(self.config_loader, 'app_language', 'en') if self.config_loader else 'en'
        lang_manager = getattr(self.config_loader, 'language_manager', None) if self.config_loader else None

        def translate_msg(raw_text: str) -> str:
            if not lang_manager:
                return raw_text
            
            parts = raw_text.split('|')
            msg_id = parts[0].strip()
            
            if not msg_id.startswith('msg_'):
                return raw_text

            kwargs = {}
            for part in parts[1:]:
                if '=' in part:
                    k, v = part.split('=', 1)
                    kwargs[k.strip()] = v.strip()
                else:
                    kwargs[f"arg{len(kwargs)}"] = part.strip()
            
            return lang_manager.get_string(lang_id, msg_id, **kwargs)
        
        if level.upper() == "RAW":
            raw_message = message.strip()
            msg_lower = raw_message.lower()
            
            log_level_for_color = "INFO"
            if msg_lower.startswith(('error:', 'validationerror:', 'exception:', 'traceback')):
                log_level_for_color = "ERROR"
            elif "out of memory" in msg_lower or "allocation failed" in msg_lower:
                log_level_for_color = "ERROR"
                
            color = log_colors.get(log_level_for_color, "default")
            self.log_signal.emit(color, translate_msg(raw_message))
        else:
            color = log_colors.get(level.upper(), "default")
            msg_str = message.strip()
            
            match = re.search(r"\[(\d+)/(\d+)\](.*)", msg_str)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                payload = match.group(3).strip()
                translated_payload = translate_msg(payload)
                
                if lang_manager:
                    text = lang_manager.get_string(lang_id, "msg_pipeline_progress", current=current, total=total, text=translated_payload)
                else:
                    text = f"Processing {current}/{total} : {translated_payload}"
                    
                self.pipeline_progress_signal.emit(current, total, text)
                self.log_signal.emit(color, f"[{level.upper()}] [{current}/{total}] {translated_payload}")
            else:
                translated_msg = translate_msg(msg_str)
                self.log_signal.emit(color, f"[{level.upper()}] {translated_msg}")
