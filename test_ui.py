import sys
from PySide6.QtWidgets import QApplication
from desktop_ui.main_window import TranslatorStudioApp

app = QApplication(sys.argv)
main_window = TranslatorStudioApp()
main_window.show()

# Print visibility of sd_base_model after 1 second
def check_visibility():
    row = main_window.setting_rows.get('sd_base_model')
    print(f"sd_base_model visible: {row.isVisible() if row else 'None'}")
    sys.exit(0)

from PySide6.QtCore import QTimer
QTimer.singleShot(1000, check_visibility)
app.exec()
