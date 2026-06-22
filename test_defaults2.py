import sys, os
from PySide6.QtWidgets import QApplication
from desktop_ui.main_window import TranslatorStudioApp
import yaml

app = QApplication(sys.argv)
window = TranslatorStudioApp()

print("--- CURRENT SETTINGS AFTER INIT (NO OLDSESSION) ---")
for key in ["detector", "ocr", "inpainter", "upscaler", "colorizer", "renderer"]:
    print(f"{key}: {window.current_settings.get(key)}")
