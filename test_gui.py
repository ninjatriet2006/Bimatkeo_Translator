import sys
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from app.core.desktop.main_window import TranslatorStudioApp

app = QApplication(sys.argv)
try:
    window = TranslatorStudioApp()
    print("MainWindow instantiated successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
