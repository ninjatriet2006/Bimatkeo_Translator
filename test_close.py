import sys, os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from desktop_ui.main_window import TranslatorStudioApp
import traceback

app = QApplication(sys.argv)
window = TranslatorStudioApp()
window.show()

def close_window():
    print("Calling window.close()...")
    window.close()
    
QTimer.singleShot(1000, close_window)

sys.exit(app.exec())
