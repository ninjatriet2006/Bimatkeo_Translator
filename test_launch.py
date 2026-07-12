import sys
from PySide6.QtWidgets import QApplication
from app.core.desktop.main_window import TranslatorStudioApp

app = QApplication.instance() or QApplication(sys.argv)
window = TranslatorStudioApp()
print("Instantiated successfully.")
