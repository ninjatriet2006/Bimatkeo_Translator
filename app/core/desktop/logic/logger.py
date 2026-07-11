import os
import re
import logging
from logging.handlers import RotatingFileHandler
from PySide6.QtCore import QObject, Signal

class QSignalLogHandler(logging.Handler):
    def __init__(self, app_logger):
        super().__init__()
        self.app_logger = app_logger

    def emit(self, record):
        self.app_logger.handle_log_record(record)

class AppLogger(QObject):
    """Handles standard python logging, formatting, coloring and progress extraction."""
    log_signal = Signal(str, str)
    pipeline_progress_signal = Signal(int, int, str)
    
    def __init__(self, config_loader=None, parent=None):
        super().__init__(parent)
        self.config_loader = config_loader
        self._setup_logging()
        
    def _setup_logging(self):
        if self.config_loader and hasattr(self.config_loader, "project_base_dir"):
            project_base_dir = self.config_loader.project_base_dir
        else:
            project_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            
        log_dir = os.path.join(project_base_dir, ".config", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates during reloads
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # 1. File Handler (Rotating)
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 2. Qt Signal Handler for UI
        signal_handler = QSignalLogHandler(self)
        # Note: Do not set formatter here, UI formatting is handled in handle_log_record
        root_logger.addHandler(signal_handler)

    def log(self, level: str, message: str):
        """Backward compatibility layer for old manual log calls."""
        lvl_map = {
            "INFO": logging.INFO,
            "SUCCESS": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "PIPELINE": logging.INFO,
            "RAW": logging.INFO,
            "DEBUG": logging.DEBUG
        }
        lvl = lvl_map.get(level.upper(), logging.INFO)
        # We pass the original "level" as an extra so the UI knows how to color it
        logging.getLogger("AppLogger").log(lvl, message, extra={"ui_level": level.upper()})

    def handle_log_record(self, record: logging.LogRecord):
        """Processes standard LogRecord from Python logging system."""
        log_colors = getattr(self.config_loader, "log_colors", {}) if self.config_loader else {}
        lang_id = getattr(self.config_loader, 'app_language', 'en') if self.config_loader else 'en'
        lang_manager = getattr(self.config_loader, 'language_manager', None) if self.config_loader else None

        raw_message = record.getMessage()

        # Handle ID translation if passed via standard extra param
        if hasattr(record, "lang_id") and lang_manager:
            kwargs = getattr(record, "lang_kwargs", {})
            raw_message = lang_manager.get_string(lang_id, record.lang_id, **kwargs)

        # Fallback for old msg_id|key=value parsing (Backward Compatibility)
        if "|" in raw_message and raw_message.split("|")[0].strip().startswith("msg_"):
            parts = raw_message.split('|')
            msg_id = parts[0].strip()
            kwargs = {}
            for part in parts[1:]:
                if '=' in part:
                    k, v = part.split('=', 1)
                    kwargs[k.strip()] = v.strip()
                else:
                    kwargs[f"arg{len(kwargs)}"] = part.strip()
            if lang_manager:
                raw_message = lang_manager.get_string(lang_id, msg_id, **kwargs)
        elif not hasattr(record, "lang_id") and lang_manager:
             # Just pass it through get_string in case it's a plain string ID without args
             raw_message = lang_manager.get_string(lang_id, raw_message)

        # Determine level/color
        ui_level = getattr(record, "ui_level", record.levelname).upper()
        if ui_level == "RAW" or not getattr(record, "ui_level", None):
            msg_lower = raw_message.lower()
            if not getattr(record, "ui_level", None):
                ui_level = record.levelname.upper()
            if ui_level == "INFO":
                if msg_lower.startswith(('error:', 'validationerror:', 'exception:', 'traceback')):
                    ui_level = "ERROR"
                elif "out of memory" in msg_lower or "allocation failed" in msg_lower:
                    ui_level = "ERROR"
        
        color = log_colors.get(ui_level, "default")

        # Progress parsing
        match = re.search(r"\[(\d+)/(\d+)\](.*)", raw_message)
        current = getattr(record, "progress_current", None)
        total = getattr(record, "progress_total", None)
        
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            payload = match.group(3).strip()
            raw_message = payload

        if current is not None and total is not None:
            if lang_manager:
                text = lang_manager.get_string(lang_id, "msg_pipeline_progress", current=current, total=total, text=raw_message)
            else:
                text = f"Processing {current}/{total} : {raw_message}"
            self.pipeline_progress_signal.emit(current, total, text)
            self.log_signal.emit(color, f"[{ui_level}] [{current}/{total}] {raw_message}")
        else:
            self.log_signal.emit(color, f"[{ui_level}] {raw_message}")
