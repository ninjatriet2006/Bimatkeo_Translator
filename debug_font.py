import sys
from PySide6.QtWidgets import QApplication
from desktop_ui.main_window import TranslatorStudioApp

app = QApplication(sys.argv)
window = TranslatorStudioApp()
font_combo = window.setting_widgets.get('font_family')
print("Combo text:", font_combo.currentText())
print("Warning property:", font_combo.property("warning"))
print("Foreground of item:", font_combo.itemData(font_combo.currentIndex(), 0)) # 0 is DisplayRole, wait, ForegroundRole is 9
from PySide6.QtCore import Qt
print("Foreground of item:", font_combo.itemData(font_combo.currentIndex(), Qt.ItemDataRole.ForegroundRole))

is_google = window._get_google_font_family_from_filename(font_combo.currentText())
print("is_google:", is_google)
