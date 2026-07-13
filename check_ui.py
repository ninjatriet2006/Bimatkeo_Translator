import sys
import os
from PySide6.QtWidgets import QApplication
from app.core.desktop.main_window import TranslatorStudioApp

app = QApplication(sys.argv)
mw = TranslatorStudioApp()
print("Children count:", len(mw.findChildren(object)))
print("Title:", mw.windowTitle())
print("Central widget layout:", mw.centralWidget().layout())
