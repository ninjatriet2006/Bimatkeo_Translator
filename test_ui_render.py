import sys, os
from PySide6.QtWidgets import QApplication, QComboBox
from desktop_ui.main_window import TranslatorStudioApp

app = QApplication(sys.argv)
window = TranslatorStudioApp()

def dump_combo(name, combo):
    print(f"--- {name} ---")
    if not combo:
        print("Not found")
        return
    print(f"Current Index: {combo.currentIndex()}")
    print(f"Current Text: '{combo.currentText()}'")
    print(f"Current Data: '{combo.currentData()}'")
    print(f"Items: {[combo.itemText(i) for i in range(combo.count())]}")

print("=== ON STARTUP ===")
dump_combo('target_lang', window.setting_widgets.get('target_lang'))
dump_combo('offline_translator', window.setting_widgets.get('offline_translator'))
dump_combo('ai_translator', window.setting_widgets.get('ai_translator'))

print("\n=== TRIGGERING TARGET LANG CHANGE ===")
window.setting_widgets.get('target_lang').setCurrentText("Vietnamese")
dump_combo('target_lang', window.setting_widgets.get('target_lang'))
dump_combo('offline_translator', window.setting_widgets.get('offline_translator'))
dump_combo('ai_translator', window.setting_widgets.get('ai_translator'))
