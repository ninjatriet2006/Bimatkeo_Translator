import sys, os
from PySide6.QtWidgets import QApplication
from desktop_ui.main_window import TranslatorStudioApp
import yaml

app = QApplication(sys.argv)
window = TranslatorStudioApp()

print("--- CURRENT SETTINGS AFTER INIT ---")
for key in ["detector", "ocr", "inpainter", "upscaler", "colorizer", "renderer"]:
    print(f"{key}: {window.current_settings.get(key)}")

print("--- OLDSESSION.YAML CONTENT ---")
with open(".config/configs/oldsession.yaml", "r") as f:
    print(f.read())
    
print("--- STUDIO_CONFIG.YAML CONTENT (defaults) ---")
with open(".config/configs/studio_config.yaml", "r") as f:
    data = yaml.safe_load(f)
    print(f"detector: {data['ui_map']['detector']['default']}")
    print(f"ocr: {data['ui_map']['ocr']['default']}")

