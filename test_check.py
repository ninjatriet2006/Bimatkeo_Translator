from app.core.desktop.config import ConfigLoader
from app.core.desktop.main_window import BimatkeoTranslator
import sys
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
mw = BimatkeoTranslator(None)
settings = mw.current_settings
missing = mw.config_loader.missing_required_fields(settings)
print("Settings detector:", settings.get("offline_detector"))
print("Missing:", missing)
print("Check model existence:", mw.config_loader.check_model_existence("paddle_onnx_v6_small", field="offline_detector"))
